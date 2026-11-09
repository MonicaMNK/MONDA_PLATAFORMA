import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const baseUrl = (__ENV.LOAD_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const courseId = __ENV.LOAD_COURSE_ID;
const token = __ENV.LOAD_BEARER_TOKEN;
const users = Number(__ENV.LOAD_USERS || 50);
const failures = new Rate("acceptance_failures");

if (!courseId || !token) {
  throw new Error("Define LOAD_COURSE_ID y LOAD_BEARER_TOKEN antes de ejecutar k6.");
}
if (!Number.isInteger(users) || users < 1) {
  throw new Error("LOAD_USERS debe ser un entero positivo.");
}

export const options = {
  scenarios: {
    warmup: {
      executor: "constant-vus",
      exec: "exerciseReadRoutes",
      vus: users,
      duration: "5m",
      tags: { phase: "warmup" },
    },
    measurement: {
      executor: "constant-vus",
      exec: "exerciseReadRoutes",
      startTime: "5m",
      vus: users,
      duration: "15m",
      tags: { phase: "measurement" },
    },
  },
  thresholds: {
    "http_req_duration{phase:measurement}": ["p(95)<800"],
    "http_req_failed{phase:measurement}": ["rate<0.01"],
    "acceptance_failures{phase:measurement}": ["rate<0.01"],
  },
};

export function exerciseReadRoutes() {
  const headers = { headers: { Authorization: `Bearer ${token}` } };
  const responses = http.batch([
    ["GET", `${baseUrl}/api/courses/${courseId}/analytics`, null, headers],
    ["GET", `${baseUrl}/api/courses/${courseId}/contents?limit=20`, null, headers],
    ["GET", `${baseUrl}/api/courses/${courseId}/reports/export?format=csv`, null, headers],
  ]);
  const endpoints = ["analytics", "contents", "export"];
  responses.forEach((response, index) => {
    const accepted = check(response, {
      [`${endpoints[index]} returns 200`]: (item) => item.status === 200,
      [`${endpoints[index]} avoids server errors`]: (item) => item.status < 500,
    });
    failures.add(!accepted, { endpoint: endpoints[index] });
  });
  sleep(0.2);
}

export function handleSummary(data) {
  const output = {};
  if (__ENV.K6_SUMMARY_PATH) {
    output[__ENV.K6_SUMMARY_PATH] = JSON.stringify(data, null, 2);
  }
  output.stdout = `k6 completed: ${users} VUs; warmup 5m; measurement 15m\n`;
  return output;
}
