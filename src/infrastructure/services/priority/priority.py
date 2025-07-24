import logging
import math
import re

import httpx
from asynciolimiter import Limiter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# Store somewhere else? Env?
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"
NIST_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NUCLEI_BASE_URL = (
    "https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/cves.json"
)
VULNCHECK_BASE_URL = "https://api.vulncheck.com/v3/index/nist-nvd2"
VULNCHECK_KEV_BASE_URL = "https://api.vulncheck.com/v3/index/vulncheck-kev"


class PriorityCalculator:
    def __init__(
        self,
        cve_list: list[str],
        epss: float = 0.2,
        cvss: float = 6.0,
        cvss_version: int = 3,
    ):
        self.cve_list = cve_list
        self.threads = list()
        self.epss_threshold = epss
        self.cvss_threshold = cvss
        self.cvss_version = cvss_version

    def check_valid_cve(self):
        valid_cve = []
        for cve in self.cve_list:
            if not re.match(r"(CVE|cve-\d{4}-\d+$)", cve):
                continue
            valid_cve.append(cve)

        self.cve_list = valid_cve

    async def get_data(self) -> dict:
        cves = {}
        # 5 requests per 30s
        rate_limiter = Limiter(5 / 30)
        for cve_id in self.cve_list:
            logger.info(f"{cve_id} searching...")
            data: dict = await rate_limiter.wrap(self.nist_check(cve_id))
            cves[cve_id] = data
            epss = await self.epss_check(cve_id)
            cves[cve_id].update(epss)
        return cves

    async def process(self) -> list:
        results = []
        cves = await self.get_data()
        for cve_id, cve_result in cves.items():
            exploited = cve_result.get("cisa_kev")
            d = {
                "cve_id": cve_id,
                "priority": self.priority_calc(exploited, cve_result),
                "epss": cve_result.get("epss"),
                "cvss": cve_result.get("cvss_baseScore"),
                "cvss_version": cve_result.get("cvss_version"),
                "severity": cve_result.get("cvss_severity"),
                # "cpe": cve_result.get("cpe"),
                "vector": cve_result.get("vector"),
            }
            if exploited:
                d["kevList"] = exploited
            results.append(d)
        return results

    async def nist_check(self, cve_id):
        """
        Function collects NVD Data
        """
        try:
            nvd_url = NIST_BASE_URL + f"?cveId={cve_id}"

            async with httpx.AsyncClient() as client:
                logging.info(f"Getting into {nvd_url}")
                response = await client.get(nvd_url)
                response.raise_for_status()

            response_data = response.json()
            if response_data.get("totalResults") > 0:
                for unique_cve in response_data.get("vulnerabilities"):
                    cisa_kev = unique_cve.get("cve").get("cisaExploitAdd", False)
                    ransomware = ""
                    if cisa_kev:
                        async with httpx.AsyncClient() as client:
                            kev_data = await client.get(CISA_KEV_URL)
                            kev_data.raise_for_status()
                        kev_list = kev_data.json()
                        for entry in kev_list.get("vulnerabilities", []):
                            if entry.get("cveID") == cve_id:
                                ransomware = str(
                                    entry.get("knownRansomwareCampaignUse")
                                ).upper()

                    cpe = (
                        unique_cve.get("cve")
                        .get("configurations", [{}])[0]
                        .get("nodes", [{}])[0]
                        .get("cpeMatch", [{}])[0]
                        .get("criteria", "cpe:2.3:::::::::::")
                    )

                    versions = ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]

                    if self.cvss_version == 4:
                        versions = [
                            "cvssMetricV40",
                            "cvssMetricV31",
                            "cvssMetricV30",
                            "cvssMetricV2",
                        ]

                    metrics = unique_cve.get("cve").get("metrics", {})

                    for version in versions:
                        if version in metrics:
                            for metric in metrics[version]:
                                return {
                                    "cvss_version": version.replace(
                                        "cvssMetric", "CVSS "
                                    ),
                                    "cvss_baseScore": float(
                                        metric.get("cvssData", {}).get("baseScore", 0)
                                    ),
                                    "cvss_severity": metric.get("cvssData", {}).get(
                                        "baseSeverity", ""
                                    ),
                                    "cisa_kev": cisa_kev,
                                    "ransomware": ransomware,
                                    "cpe": cpe,
                                    "vector": metric.get("cvssData", {}).get(
                                        "vectorString", ""
                                    ),
                                }

                    if unique_cve.get("cve").get("vulnStatus") == "Awaiting Analysis":
                        logger.info(f"{cve_id} - Awaiting NVD Analysis")
                        return {
                            "cvss_version": "",
                            "cvss_baseScore": "",
                            "cvss_severity": "",
                            "cisa_kev": "",
                            "ransomware": "",
                            "cpe": "",
                            "vector": "",
                        }
            else:
                logger.warning(f"{cve_id} - Not Found in NIST NVD.")
                return {
                    "cvss_version": "",
                    "cvss_baseScore": "",
                    "cvss_severity": "",
                    "cisa_kev": "",
                    "ransomware": "",
                    "cpe": "",
                    "vector": "",
                }
        except httpx.NetworkError:
            logger.error(
                f"""
                {cve_id} - Unable to connect to NIST NVD
                Check your Internet connection or try again
                """
            )
        except httpx.TimeoutException:
            logger.error(f"{cve_id} - The request to NIST NVD timed out")
        except httpx.HTTPError as exc:
            logger.error(f"{cve_id} - Error due to {exc}")
        except ValueError as val_err:
            logger.error(f"{cve_id} - Error processing the response: {val_err}")

        return {
            "cvss_version": "",
            "cvss_baseScore": "",
            "cvss_severity": "",
            "cisa_kev": "",
            "ransomware": "",
            "cpe": "",
            "vector": "",
        }

    async def epss_check(self, cve_id) -> dict:
        """
        Function collects EPSS from FIRST.org
        """
        try:
            epss_url = EPSS_URL + f"?cve={cve_id}"
            async with httpx.AsyncClient() as client:
                epss_response = await client.get(epss_url)
                epss_response.raise_for_status()

            response_data = epss_response.json()
            if response_data.get("total") > 0:
                for cve in response_data.get("data"):
                    results = {
                        "epss": float(cve.get("epss")),
                        "percentile": int(float(cve.get("percentile")) * 100),
                    }
                    return results
            else:
                logger.warning(f"{cve_id} - Not Found in EPSS.")
                return {"epss": None, "percentile": None}
        except httpx.NetworkError:
            logger.error(
                f"""
                {cve_id} - Unable to connect to EPSS
                Check your Internet connection or try again"
                """
            )
        except httpx.TimeoutException:
            logger.error(f"{cve_id} - The request to EPSS timed out")
        except httpx.HTTPError as exc:
            logger.error(f"{cve_id} - HTTP error occurred: {exc}")
        except ValueError as val_err:
            logger.error(f"{cve_id} - Error processing the response: {val_err}")

        return {"epss": None, "percentile": None}

    def priority_calc(self, exploited, cve_result):
        if exploited:
            return "1+"

        cvss = float(cve_result.get("cvss_baseScore", -math.inf))
        epss = float(cve_result.get("epss", -math.inf))

        if cvss >= self.cvss_threshold:
            if epss >= self.epss_threshold:
                return "1"
            return "2"
        if epss >= self.epss_threshold:
            return "3"
        return "4"
