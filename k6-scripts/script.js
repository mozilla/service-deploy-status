// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Uses:
//
// BASEURL - protocol and host of server to load test--exclude ending slash

import http from 'k6/http';
import { SharedArray } from 'k6/data';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.5.0/index.js';

const testData = new SharedArray('test urls', function () {
  return JSON.parse(open('./test_urls.json'));
});

export default function () {
  const baseurl = (__ENV.BASEURL || 'http://web:8000').replace(/\/$/, "");

  for (const testCase of testData) {
    if (randomIntBetween(0, 100) <= testCase['percent']) {
      http.get(`${baseurl}${testCase['path']}`);
    }
  }
};
