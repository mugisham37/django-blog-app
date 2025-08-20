/**
 * Stress testing script using k6
 * Tests the system under extreme load to find breaking points
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend, Counter } from "k6/metrics";

// Custom metrics
const errorRate = new Rate("errors");
const requestDuration = new Trend("request_duration");
const requestCount = new Counter("total_requests");

export const options = {
  stages: [
    { duration: "1m", target: 10 }, // Warm up
    { duration: "2m", target: 50 }, // Ramp up to 50 users
    { duration: "3m", target: 100 }, // Ramp up to 100 users
    { duration: "5m", target: 200 }, // Stress test with 200 users
    { duration: "3m", target: 300 }, // Push to 300 users
    { duration: "2m", target: 400 }, // Peak stress with 400 users
    { duration: "1m", target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000"], // Allow higher response times under stress
    http_req_failed: ["rate<0.3"], // Allow higher error rate under stress
    errors: ["rate<0.3"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/api/v1";

export default function () {
  requestCount.add(1);

  // Stress test scenarios
  const scenario = Math.random();

  if (scenario < 0.5) {
    // 50% - Heavy blog browsing
    stressBlogBrowsing();
  } else if (scenario < 0.8) {
    // 30% - Concurrent post reading
    stressPostReading();
  } else {
    // 20% - Search stress
    stressSearch();
  }

  sleep(0.1); // Minimal think time for stress testing
}

function stressBlogBrowsing() {
  const responses = http.batch([
    ["GET", `${BASE_URL}/blog/posts/`],
    ["GET", `${BASE_URL}/blog/categories/`],
    ["GET", `${BASE_URL}/blog/tags/`],
  ]);

  responses.forEach((response, index) => {
    const isSuccess = check(response, {
      "status is 200": (r) => r.status === 200,
    });

    requestDuration.add(response.timings.duration);
    errorRate.add(!isSuccess);
  });
}

function stressPostReading() {
  // Simulate reading multiple posts quickly
  const listResponse = http.get(`${BASE_URL}/blog/posts/?page_size=10`);

  if (listResponse.status === 200) {
    try {
      const listData = JSON.parse(listResponse.body);
      if (listData.results && listData.results.length > 0) {
        // Read 3 random posts concurrently
        const randomPosts = listData.results
          .sort(() => 0.5 - Math.random())
          .slice(0, 3);

        const postRequests = randomPosts.map((post) => [
          "GET",
          `${BASE_URL}/blog/posts/${post.slug}/`,
        ]);

        const postResponses = http.batch(postRequests);

        postResponses.forEach((response) => {
          const isSuccess = check(response, {
            "post detail status is 200": (r) => r.status === 200,
          });

          requestDuration.add(response.timings.duration);
          errorRate.add(!isSuccess);
        });
      }
    } catch (e) {
      errorRate.add(true);
    }
  }
}

function stressSearch() {
  const searchTerms = [
    "test",
    "blog",
    "api",
    "stress",
    "performance",
    "load",
    "system",
  ];
  const randomTerms = searchTerms.sort(() => 0.5 - Math.random()).slice(0, 3);

  const searchRequests = randomTerms.map((term) => [
    "GET",
    `${BASE_URL}/blog/posts/?search=${term}`,
  ]);

  const searchResponses = http.batch(searchRequests);

  searchResponses.forEach((response) => {
    const isSuccess = check(response, {
      "search status is 200": (r) => r.status === 200,
    });

    requestDuration.add(response.timings.duration);
    errorRate.add(!isSuccess);
  });
}
