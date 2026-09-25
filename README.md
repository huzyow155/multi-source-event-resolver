# Multi-Source Event Resolver (GenLayer Intelligent Contract Primitive)

A decentralized, AI-powered subjective truth oracle primitive built for GenLayer. This intelligent contract cross-references two independent news or evidence URLs against a natural-language event description and reaches network-wide consensus on whether the event definitively occurred.

---

## 1. Overview & Builder Program Value

In decentralized applications, real-world subjective event resolution has historically required centralized multi-sigs, fragile oracles (e.g., UMA with multi-day dispute delays), or manual token-voting markets.

With GenLayer:
1. **Direct Web Access On-Chain:** Nodes render live web pages directly via `gl.nondet.web.render`.
2. **Subjective AI Reasoning:** Nodes analyze textual nuances, verify claims, and classify evidence via `gl.nondet.exec_prompt`.
3. **Optimistic Democracy & Semantic Equivalence:** Validators independently cross-check both sources and compare their verdict (`HAPPENED`, `NOT_HAPPENED`, `CONFLICTING_EVIDENCE`, `UNRESOLVED`) using `gl.vm.run_nondet`. Consensus is formed on the **semantic meaning** rather than brittle character-by-character string matching.

This primitive serves as an architectural building block for:
- **Prediction Markets** (e.g., automated resolution for Polymarket/Augur-style prediction markets).
- **Parametric Insurance** (e.g., flight cancellations, natural disaster verification, logistics milestones).
- **DAO Governance & Milestone Escrows** (e.g., verifying product launch or regulatory approval before releasing funds).

---

## 2. Deployment & Real On-Chain Evidence

- **Network:** `studionet` (GenLayer Studio RPC: `https://studio.genlayer.com/api`)
- **Active Contract Address:** [`0xe594F4FCD0A55fE72281c99F1B7872993039a4f8`](https://genlayer-explorer.vercel.app/address/0xe594F4FCD0A55fE72281c99F1B7872993039a4f8)
- **Chain ID:** `61999`
- **Contract File:** `contracts/contract.py`
- **Superseded Staging Addresses:** `0xC572A5Fd491CA167967e2b3964f83382225d213c` (superseded initial deployment; lacked dual-dict response parsing) and `0x9B6be06E7Eca76D9D559D30D8697E53090e686Ae` (superseded prototype).

### Live Query Verification (Real Result)
The contract is deployed and actively verifiable on `studionet`. Querying the live contract state via the GenLayer Python SDK (`genlayer-py`):

```python
import genlayer_py
from eth_account import Account

account = Account.create()
client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
count = client.read_contract(
    address="0xe594F4FCD0A55fE72281c99F1B7872993039a4f8",
    function_name="get_event_count",
    args=[]
)
# REAL RESULT returned from live studionet RPC:
# 4
```

---

### Real Resolution Evidence (Live On-Chain Transactions)

The contract was tested against four distinct real-world scenarios on `studionet`. Below are the actual transaction hashes and the exact records retrieved from contract storage via `get_event()`:

#### Scenario A: Affirmative Resolution (`HAPPENED`)
* **Event ID:** `evt-python-creator-guido`
* **Claim:** "The Python programming language was created by Guido van Rossum"
* **Source 1:** `https://raw.githubusercontent.com/python/cpython/main/README.rst`
* **Source 2:** `https://en.wikipedia.org/wiki/Guido_van_Rossum`
* **Transaction Hash:** [`0xea09d112d9f1134401cd5af2d5099310ce9cf7e5b09bd640d607da5153bda113`](https://genlayer-explorer.vercel.app/tx/0xea09d112d9f1134401cd5af2d5099310ce9cf7e5b09bd640d607da5153bda113)
* **Real Consensus State Record (Read from `get_event("evt-python-creator-guido")`):**
```json
{
  "id": "evt-python-creator-guido",
  "event_description": "The Python programming language was created by Guido van Rossum",
  "url1": "https://raw.githubusercontent.com/python/cpython/main/README.rst",
  "url2": "https://en.wikipedia.org/wiki/Guido_van_Rossum",
  "verdict": "HAPPENED",
  "confidence": "MEDIUM",
  "source1_status": "NEUTRAL",
  "source2_status": "CONFIRMS",
  "summary": "Source 2 explicitly states that Guido van Rossum is the creator of the Python programming language. Source 1 is a CPython README and does not mention who created Python, so it is neutral rather than contradictory.",
  "resolver": "0x4cF02aA2e7F472D06e7790D53C526164ff4988e8"
}
```

#### Scenario B: Refuted Claim (`NOT_HAPPENED`)
* **Event ID:** `evt-armstrong-mars-1969`
* **Claim:** "Astronaut Neil Armstrong landed on planet Mars during the 1969 space mission"
* **Source 1:** `https://en.wikipedia.org/wiki/Neil_Armstrong`
* **Source 2:** `https://raw.githubusercontent.com/nasa/nasa-3d-resources/master/README.md`
* **Transaction Hash:** [`0x9b22e1a79060b05511136daa3b29aded2744d6b9b5c400dd8a2be55761c272dc`](https://genlayer-explorer.vercel.app/tx/0x9b22e1a79060b05511136daa3b29aded2744d6b9b5c400dd8a2be55761c272dc)
* **Real Consensus State Record (Read from `get_event("evt-armstrong-mars-1969")`):**
```json
{
  "id": "evt-armstrong-mars-1969",
  "event_description": "Astronaut Neil Armstrong landed on planet Mars during the 1969 space mission",
  "url1": "https://en.wikipedia.org/wiki/Neil_Armstrong",
  "url2": "https://raw.githubusercontent.com/nasa/nasa-3d-resources/master/README.md",
  "verdict": "NOT_HAPPENED",
  "confidence": "HIGH",
  "source1_status": "REFUTES",
  "source2_status": "NEUTRAL",
  "summary": "Source 1 explicitly states that Neil Armstrong landed on the Moon, not Mars, during the 1969 Apollo 11 mission, directly refuting the event. Source 2 is a README for a 3D resources repository and is entirely neutral/irrelevant to the event.",
  "resolver": "0x4cF02aA2e7F472D06e7790D53C526164ff4988e8"
}
```

#### Scenario C: Inaccessible / Inconclusive Evidence (`UNRESOLVED`)
* **Event ID:** `evt-unresolved-sources`
* **Claim:** "Secret undocumented merger agreement signed between Acme Corp and Omni Corp"
* **Source 1:** `https://raw.githubusercontent.com/nonexistent-org-12345/nonexistent-repo/main/404.txt`
* **Source 2:** `https://httpstat.us/404`
* **Transaction Hash:** [`0x7095534ad546d9479c78ef5deef593a86a432a3f60d0cf372eb9da5741261a5b`](https://genlayer-explorer.vercel.app/tx/0x7095534ad546d9479c78ef5deef593a86a432a3f60d0cf372eb9da5741261a5b)
* **Real Consensus State Record (Read from `get_event("evt-unresolved-sources")`):**
```json
{
  "id": "evt-unresolved-sources",
  "event_description": "Secret undocumented merger agreement signed between Acme Corp and Omni Corp",
  "url1": "https://raw.githubusercontent.com/nonexistent-org-12345/nonexistent-repo/main/404.txt",
  "url2": "https://httpstat.us/404",
  "verdict": "UNRESOLVED",
  "confidence": "HIGH",
  "source1_status": "UNAVAILABLE",
  "source2_status": "UNAVAILABLE",
  "summary": "Both sources failed to load and returned error messages, providing no evidence to verify or refute the claimed merger agreement.",
  "resolver": "0xe2720b79488e328fe35f35a700e41efa33846aea"
}
```

#### Scenario D: Live Reuters Paywall/Bot-Block Test (`UNAVAILABLE` Source Analysis)
* **Event ID:** `evt-spacex-reuters-unresolved`
* **Claim:** "SpaceX caught the Super Heavy booster of Starship during flight 5"
* **Source 1:** `https://en.wikipedia.org/wiki/Starship_integrated_flight_test_5`
* **Source 2:** `https://www.reuters.com/technology/space/spacex-launches-fifth-starship-test-flight-aims-booster-catch-2024-10-13/`
* **Transaction Hash:** [`0x833426596d80a42f6443fcca6d438c339f3fee64c40484fd5352573297c23f77`](https://genlayer-explorer.vercel.app/tx/0x833426596d80a42f6443fcca6d438c339f3fee64c40484fd5352573297c23f77)
* **Real Consensus State Record (Read from `get_event("evt-spacex-reuters-unresolved")`):**
```json
{
  "id": "evt-spacex-reuters-unresolved",
  "event_description": "SpaceX caught the Super Heavy booster of Starship during flight 5",
  "url1": "https://en.wikipedia.org/wiki/Starship_integrated_flight_test_5",
  "url2": "https://www.reuters.com/technology/space/spacex-launches-fifth-starship-test-flight-aims-booster-catch-2024-10-13/",
  "verdict": "HAPPENED",
  "confidence": "MEDIUM",
  "source1_status": "CONFIRMS",
  "source2_status": "UNAVAILABLE",
  "summary": "Source 1 explicitly states that Starship flight test 5 was the first catch of a returning Super Heavy booster at the launch tower. Source 2 was unavailable, so the conclusion relies on Source 1 without any contradictory evidence.",
  "resolver": "0x4cF02aA2e7F472D06e7790D53C526164ff4988e8"
}
```

> **Web Scraping Limitation Note:** Commercial news outlets (such as Reuters, Bloomberg, or the New York Times) employ anti-bot shields (Cloudflare Turnstile, Akamai, or mandatory JavaScript paywall interstitial gates). When fetched by node web rendering workers, these endpoints return 403 Forbidden or challenge shells, flagging `source_status: UNAVAILABLE`. For reliable on-chain resolution, use public documentation, institutional repositories, government feeds, or open encyclopedic mirrors (e.g. Wikipedia).

---

## 3. How Consensus & Validator Equivalence Works

A primary challenge with LLMs on-chain is non-determinism: two honest validator nodes querying identical prompts may receive slightly different wording, punctuation, or formatting in their natural language explanations.

If a contract compared raw string outputs, validators would inevitably disagree, causing consensus stalls and transaction failures.

### The Semantic Consensus Pattern
The contract solves this through GenLayer's Equivalence Principle:
1. **Isolated Execution:** All non-deterministic operations (`gl.nondet.web.render`, `gl.nondet.exec_prompt`) are quarantined inside an inner routine (`execute_cross_check`) that accesses no contract storage or `self`.
2. **Leader Proposal:** The transaction leader executes `execute_cross_check()`, which fetches both URLs, invokes the LLM with structured prompt instructions, and normalizes the parsed verdict into one of four canonical states:
   - `HAPPENED`
   - `NOT_HAPPENED`
   - `CONFLICTING_EVIDENCE`
   - `UNRESOLVED`
3. **Independent Validation:** When the validator executes `validator_fn(leaders_res)`, it independently fetches the sources and re-runs the LLM assessment locally (`my_data = execute_cross_check()`).
4. **Semantic Verdict Matching:**
   ```python
   # The validator checks semantic meaning (the verdict), NOT syntactic wording:
   return my_data.get("verdict") == leader_verdict
   ```
   Only `verdict` is consensus-verified; confidence, summary, source1_status, source2_status are leader-reported and not independently checked by validators. Variations in the free-form `summary` text or token phrasing are explicitly ignored. As long as validators agree on the objective truth classification (`verdict`), consensus is achieved.

---

## 4. GenVM Runtime Compliance

| Rule | Status | Implementation Details |
| :--- | :--- | :--- |
| **Pragma Header** | Verified | Line 1: `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`<br>Line 2: `from genlayer import *` |
| **Consensus API** | Verified | Uses sandboxed `gl.vm.run_nondet(leader_fn, validator_fn)` for Optimistic Democracy consensus. |
| **Root-Domain Validation** | Verified | Pure Python helper `get_domain` parses effective registrable root domains, preventing same-domain source spoofing across subdomains. |
| **Storage Collections** | Verified | Uses `TreeMap[str, EventResolution]` and `DynArray[str]`. Collections are auto-initialized by GenVM; `__init__` only assigns scalar `self.resolution_count = bigint(0)`. |
| **Type Discipline** | Verified | No bare `int`, `float`, `list`, or `dict` in storage. Calldata types strictly adhere to GenVM ABI requirements (`str`, `int`, `bool`, `Address`). |
| **Storage Dataclass** | Verified | Custom record `EventResolution` decorated with `@allow_storage` and `@dataclass`. |
| **Character Encoding** | Verified | 100% pure 7-bit ASCII encoding throughout code and documentation. |
| **Fail-Closed Security** | Verified | Any network render failure or malformed LLM payload gracefully falls back to `UNRESOLVED` rather than halting the VM. |
| **State Protection** | Verified | Post-nondet race check prevents double-writes if an event resolves concurrently during validation. |

---

## 5. Public API Specification

### State-Changing Methods (`@gl.public.write`)
* `resolve_event(event_id: str, event_description: str, url1: str, url2: str)`:
  Fetches both sources, executes cross-checking consensus, and records the resolution in storage.
  * **Registrable Root-Domain Validation:** Enforces that `url1` and `url2` originate from distinct root domains using `get_domain()`. Handles two-part country code TLDs (e.g. `bbc.co.uk` and `sports.bbc.co.uk` are identified as the same domain and rejected).
  * **Known Limitations:** `get_domain()` is a simplified suffix matcher, not a full public suffix list, so multi-tenant hosts like `raw.githubusercontent.com`, `github.io`, `vercel.app` etc. collapse to one domain - two genuinely independent sources on the same multi-tenant host will be incorrectly rejected as non-independent.
  * Reverts with `gl.vm.UserError` if:
    - `event_id` is empty or already resolved (preventing double claims / state corruption).
    - `event_description` contains fewer than 5 characters.
    - `url1` or `url2` do not use `http://` or `https://`.
    - `get_domain(url1) == get_domain(url2)` ("url1 and url2 must belong to different independent root domains").
    - Event resolution state collision detected post-validation (concurrency safety).

### Read-Only Query Methods (`@gl.public.view`)
* `get_event(event_id: str) -> EventResolution`: Returns the complete stored record for the given event ID. Reverts if not found.
* `has_event(event_id: str) -> bool`: Returns `True` if the event has been resolved, `False` otherwise.
* `get_event_count() -> bigint`: Returns the total count of resolved events.
* `get_event_id_at(index: bigint) -> str`: Returns the event ID at index in the chronological log (for off-chain indexing).
* `get_latest_event() -> EventResolution`: Returns the most recently resolved event. Reverts if no events exist.

---

## 6. Running Tests

The test suite runs using `gltest` (the official GenLayer testing framework):

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run all unit & integration tests
gltest tests/ -v
```

All 7 test cases pass covering initial state, affirmative resolution (`HAPPENED`), refutation (`NOT_HAPPENED`), contradiction (`CONFLICTING_EVIDENCE`), inconclusive evidence (`UNRESOLVED`), double-claim prevention, and input validation.
