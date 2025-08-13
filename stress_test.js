import http from 'k6/http';

import { check, sleep, group } from 'k6';

export const options = {
  vus: 50,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASEURL = 'http://localhost:8080';

export default function () {
  group('Login', function(){
    const data = { username: 'admin', password: 'Password@123'}
    let login = http.post(`${BASEURL}/auth/login`, data)
    check(login, {
      'GET / status is 200': (r) => r.status === 200,
    });
    const res = http.get(`${BASEURL}/`)
    check(res, {
      'GET / status is 200': (r) => r.status === 200,
    })
    sleep(1);
  });
};
