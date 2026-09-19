# Multi-Source Event Resolver (GenLayer Intelligent Contract Primitive)

A decentralized, AI-powered truth oracle primitive built for GenLayer. This intelligent contract cross-references two independent news or evidence URLs against a natural-language event description and reaches network-wide consensus on whether the event definitively occurred.

---

## 1. Overview & Builder Program Value

In decentralized applications, real-world subjective event resolution has historically required centralized multi-sigs, fragile oracles (e.g., UMA with multi-day dispute delays), or manual token-voting markets.

With GenLayer:
1. **Direct Web Access On-Chain:** Nodes render live web pages directly via `gl.nondet.web.render`.
2. **Subjective AI Reasoning:** Nodes analyze textual nuances, verify claims, and classify evidence via `gl.nondet.exec_prompt`.
3. **Optimistic Democracy & Semantic Equivalence:** Validators independently cross-check both sources and compare their verdict (`HAPPENED`, `NOT_HAPPENED`, `CONFLICTING_EVIDENCE`, `UNRESOLVED`) using `gl.vm.run_nondet_unsafe`. Consensus is formed on the **semantic meaning** rather than brittle character-by-character string matching.

This primitive serves as an architectural building block for:
- **Prediction Markets** (e.g., Polymarket / Augur-style automated resolution without centralized resolvers).
- **Parametric Insurance** (e.g., flight cancellations, natural disaster verification, logistics milestones).
- **DAO Governance & Milestone Escrows** (e.g., verifying product launch or regulatory approval before releasing funds).

---

## 2. Deployment

- **Network:** `studionet` (GenLayer Studio RPC: `https://studio.genlayer.com/api`)
- **Contract Address:** `0x9B6be06E7Eca76D9D559D30D8697E53090e686Ae`
- **Chain ID:** `61999`
- **Contract File:** `contracts/contract.py`

### Live Query Verification (Real Result)
The contract is deployed and actively verifiable on `studionet`. Using the GenLayer Python SDK (`genlayer-py`), querying the read-only contract state returns:

```python
import genlayer_py

client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
count = client.read_contract(
    address="0x9B6be06E7Eca76D9D559D30D8697E53090e686Ae",
    function_name="get_event_count",
    args=[]
)
# REAL RESULT returned from studionet RPC:
# 0
```

### Worked Resolution Example (Input & Expected Output)

**Transaction Call (`resolve_event`):**
```python
contract.resolve_event(
    event_id="spacex-starship-ift5",
    event_description="SpaceX successfully caught the Super Heavy booster of Starship during flight 5",
    url1="https://en.wikipedia.org/wiki/Starship_integrated_flight_test_5",
    url2="https://www.reuters.com/technology/space/spacex-launches-fifth-starship-test-flight-aims-booster-catch-2024-10-13/"
)
```

**Expected Consensus State Record (`get_event("spacex-starship-ift5")`):**
```json
{
  "id": "spacex-starship-ift5",
  "event_description": "SpaceX successfully caught the Super Heavy booster of Starship during flight 5",
  "url1": "https://en.wikipedia.org/wiki/Starship_integrated_flight_test_5",
  "url2": "https://www.reuters.com/technology/space/spacex-launches-fifth-starship-test-flight-aims-booster-catch-2024-10-13/",
  "verdict": "HAPPENED",
  "confidence": "HIGH",
  "source1_status": "CONFIRMS",
  "source2_status": "CONFIRMS",
  "summary": "Both independent news sources confirm that SpaceX successfully caught the Super Heavy booster on the launch tower arms during Flight 5.",
  "resolver": "0x2bd806c97F0e00aF1a1fC3328fA763a9269723C8"
}
```

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
   Variations in the free-form `summary` text or token phrasing are explicitly ignored. As long as validators agree on the objective truth classification (`verdict`), consensus is achieved.

---

## 4. GenVM Runtime Compliance

| Rule | Status | Implementation Details |
| :--- | :--- | :--- |
| **Pragma Header** | Verified | Line 1: `# v0.2.16`<br>Line 2: `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`<br>Line 3: `from genlayer import *` |
| **Storage Collections** | Verified | Uses `TreeMap[str, EventResolution]` and `DynArray[str]`. Collections are auto-initialized by GenVM; `__init__` only assigns scalar `self.resolution_count = bigint(0)`. |
| **Type Discipline** | Verified | No bare `int`, `float`, `list`, or `dict` in storage. Calldata types strictly adhere to GenVM ABI requirements (`str`, `int`, `bool`, `Address`). |
| **Storage Dataclass** | Verified | Custom record `EventResolution` decorated with `@allow_storage` and `@dataclass`. |
| **Character Encoding** | Verified | 100% pure 7-bit ASCII encoding throughout code and documentation. |
| **Fail-Closed Security** | Verified | Any network render failure or malformed LLM payload gracefully falls back to `UNRESOLVED` rather than halting the VM. |

---

## 5. Public API Specification

### State-Changing Methods (`@gl.public.write`)
* `resolve_event(event_id: str, event_description: str, url1: str, url2: str)`:
  Fetches both sources, executes cross-checking consensus, and records the resolution in storage.
  * Reverts with `gl.vm.UserError` if:
    - `event_id` is empty or already resolved (preventing double claims / state corruption).
    - `event_description` contains fewer than 5 characters.
    - `url1` or `url2` do not use `http://` or `https://`.
    - `url1 == url2` (enforces source independence).

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
