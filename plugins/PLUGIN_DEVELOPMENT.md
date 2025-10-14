# ThreatVault Plugin Development Guide

## 1. Overview

A plugin in ThreatVault is a Python module that transforms uploaded CSV data into a Polars LazyFrame with a specific schema. Your plugin will be run through a verification step to ensure:

1. It can process uploaded files without error.
2. It produces the expected columns and data types.
3. It follows specific rules for VA (Vulnerability Assessment) or Compliance workflows.

## 2. Plugin Structure

Plugins are organized in the following directory structure:

```
plugins/
├── builtin/           # Built-in plugins provided with ThreatVault
│   ├── ha/            # Host Assessment/Compliance plugins
│   └── va/            # Vulnerability Assessment plugins
└── custom/            # Custom plugins directory for your implementations
    ├── ha/            # Custom Host Assessment/Compliance plugins
    └── va/            # Custom Vulnerability Assessment plugins
```

## 3. Plugin Types

ThreatVault supports two types of plugins:

1. **Vulnerability Assessment (VA)** - Process vulnerability scan data from security tools
2. **Compliance/Host Assessment (HA)** - Process host configuration and compliance data

## 4. Plugin Lifecycle

Here's what happens under the hood when your plugin runs:

1. **File ingestion**
   - The system reads one or more uploaded CSV files.

2. **Plugin execution**
   - Your plugin's `process(data: bytes)` function is called.
   - The function must return either:
     - A Polars LazyFrame (`pl.LazyFrame`)
     - A Polars DataFrame (`pl.DataFrame`) – will be converted to LazyFrame
     - A Pandas DataFrame – will be converted to Polars LazyFrame

3. **Schema verification**
   - The system validates your output against the required schema.
   - If column names or data types do not match, the system raises an `InvalidInput` exception.

## 5. Required Schema

Your plugin must produce a DataFrame or LazyFrame with these exact columns and types.
- ✅ Order does not matter, but names and types must match.
- ❌ Extra or missing columns are not allowed.

### VA Plugin Schema

| Column      | Type        | Description                                   |
|-------------|-------------|-----------------------------------------------|
| cve         | pl.String() | CVE identifier (e.g., CVE-2023-12345)         |
| risk        | pl.String() | Risk level (see acceptable values below)      |
| host        | pl.String() | Host/IP where the issue was found             |
| port        | pl.Int64()  | Port number                                   |
| name        | pl.String() | Finding name                                  |
| description | pl.String() | Human-readable explanation of the finding     |
| remediation | pl.String() | How to fix the issue                          |
| evidence    | pl.String() | Proof/details of the finding                  |
| vpr_score   | pl.String() | Vendor or risk score                          |

### Compliance/HA Plugin Schema

| Column      | Type        | Description                                   |
|-------------|-------------|-----------------------------------------------|
| risk        | pl.String() | Risk level (see acceptable values below)      |
| host        | pl.String() | Host/IP where the issue was found             |
| port        | pl.Int64()  | Port number (default 0)                       |
| name        | pl.String() | Finding name                                  |
| description | pl.String() | Human-readable explanation of the finding     |
| remediation | pl.String() | How to fix the issue                          |
| evidence    | pl.String() | Proof/details of the finding                  |
| status      | pl.String() | Finding status (see acceptable values below)  |

## 6. Acceptable Values

### Risk

- CRITICAL
- HIGH
- MEDIUM
- LOW
- None (Only for Compliance)

**Important Notes:**
- `None` must not be a string. Make sure that it's not stringified.
- For Compliance: `None` will be defaulted to MEDIUM
- For VA: `None` is not a valid value
- Risk will be referred to as severity internally

### Status

#### VA
- NEW
- OPEN
- CLOSED
- EXEMPTION
- OTHERS

Even EXEMPTION and OTHERS are valid values but these typically are set manually rather than uploaded.

#### Compliance
- PASSED
- FAILED
- WARNING

## 7. VA vs Compliance Plugins

Your plugin's output is treated differently depending on whether it's used for VA or Compliance (HA).

### VA Plugins
- Everything must be provided by the plugin.
- All fields (risk, description, etc.) must already be populated.
- The system does not fill defaults for you.

### Compliance Plugins
For compliance plugins, the system will apply post-processing before saving findings:

```python
# Example of what happens automatically
self.finding_lf = self.finding_lf.with_columns(
    # Default severity
    severity=pl.col("risk").fill_null(SeverityEnum.MEDIUM.value),
    # Ensure evidence not null
    evidence=pl.col("evidence").fill_null(""),                 
)
```

You should output risk as null if unknown, not as an empty string ("").

## 8. Example Plugin Templates

Note that the plugin must accept bytes, not a filename.

### Using Polars

```python
import polars as pl

def process(data: bytes) -> pl.LazyFrame:
    df = pl.read_csv(data)
    df = df.with_columns(
        risk=pl.when(pl.col("risk") == "")
                .then(None)  # Ensure null for HA workflow
                .otherwise(pl.col("risk"))
    )

    # Optional: can just return the dataframe
    return df.lazy()
```

### Using Pandas

Note that in pandas you need to convert bytes into BytesIO:

```python
import pandas as pd
import io

def process(data: bytes) -> pd.DataFrame:
    data_csv = io.BytesIO(data)
    df = pd.read_csv(data_csv)
    # Do necessary transformation

    return df
```

## 9. Development Process

### Creating a New Plugin

1. Create a new Python file in the appropriate directory:
   - For VA plugins: `plugins/custom/va/your_plugin_name.py`
   - For HA plugins: `plugins/custom/ha/your_plugin_name.py`

2. Implement the `process` function that accepts data in bytes format and returns a DataFrame or LazyFrame

3. Ensure your plugin handles data transformation and normalization according to the required schema

### Best Practices

1. **Data Cleaning**:
   - Replace newlines with HTML line breaks (`<br/>`) for text fields
   - Normalize column names to lowercase with underscores
   - Handle missing values appropriately

2. **Performance**:
   - Use polars LazyFrame for efficient data processing
   - Minimize memory usage for large files
   - Use lazy operations when possible

3. **Error Handling**:
   - Implement robust error handling for malformed input files
   - Provide meaningful error messages

## 10. Testing Your Plugin

To test your plugin:

1. Place your input file in a test directory
2. Create a test script that loads the file and passes it to your plugin's `process` function
3. Verify that the output has the correct schema and data
4. (Optional) Run the Verify function in the plugin management page

## 11. Checklist

✅ Before submitting your plugin, verify:
- Plugin is a valid .py file
- Output matches the required schema (names + types)
- No missing required columns
- risk is null (not "") when not present (HA only)
- No runtime exceptions when processing real-world data

## 12. Integration

Once your plugin is developed and tested, it will be automatically discovered by ThreatVault when placed in the appropriate directory. The plugin name will be derived from the filename (without the `.py` extension).

## 13. Troubleshooting

Common issues:

1. **Schema mismatch**: Ensure your plugin returns all required columns with the correct data types
2. **Memory errors**: Use lazy evaluation and avoid collecting large DataFrames into memory
3. **File format issues**: Ensure your plugin can handle the specific format of your input files

For additional help, refer to the polars documentation: https://pola-rs.github.io/polars/