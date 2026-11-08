
## Tools

- ChatGPT: Helped explain the task, identify the required test scenarios, and review test coverage against the specification.
- pytest: Used to run the test suite.
- FastAPI TestClient: Used to test HTTP endpoints.
- jsonschema: Used to validate transfer cards against the JSON Schema contract.

## What AI got wrong

The initial inbox test approach used different destination branches, which could not verify priority ordering within a single inbox. The test was revised to send transfers with different priorities to the same destination branch.


## In my own words

### 1. Pick one mutant your first draft of tests did not kill. Why not, and what did you add?

One mutant my first draft did not kill was M10 (inbox ignores priority). Initially, I was testing transfers going to different branches, so I wasn't actually checking how transfers were sorted inside the same inbox. I fixed this by creating multiple transfers with different priorities going to the same destination branch, then checking that they were returned in the correct order: urgent, high, and normal. I also checked that transfers with the same priority kept their request order.

### 2. Why is a test that only asserts status_code == 409 weaker than one that asserts the problem type?

Because a 409 status code only tells me that a conflict happened, but it doesn't tell me whether it happened for the correct reason. For example, a transfer might be rejected because it is already approved or because it would leave the source branch below its reserve. Both return 409, but they represent different problems. Checking the problem type makes sure the API returns the correct error for the specific situation, not just the correct status code.

