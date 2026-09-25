# Prior Art & Differentiation Analysis

## Referenced Prior Art
* **Project:** `yarima18/Multi-Source-Claim-Event-Resolver`
* **Reference Repository:** [yarima18/Multi-Source-Claim-Event-Resolver](https://github.com/yarima18/Multi-Source-Claim-Event-Resolver)

---

## Technical Comparison & Verified Differentiations

While both contracts explore multi-source event resolution for subjective oracles on GenLayer, this implementation introduces critical architectural and security improvements:

### 1. Registrable Root-Domain Independence (Security & Anti-Sybil)
* **Prior Art (`yarima18`):** Checked naive string equality (`url1 != url2`). This allowed two URLs from the exact same publisher or organization (e.g., `news.bbc.co.uk/story-a` and `sports.bbc.co.uk/story-b`, or `blog.company.com/p1` and `press.company.com/p2`) to pass as "independent sources".
* **This Implementation:** Implements true registrable root-domain extraction (`get_domain`) recognizing common multi-part public suffixes (such as `.co.uk`, `.com.au`, `.org.uk`, etc.). Any URLs sharing the same effective root domain are rejected with `gl.vm.UserError("url1 and url2 must belong to different independent root domains")`, ensuring genuine source diversity.

### 2. Upgraded Non-Deterministic Consensus (`gl.vm.run_nondet`)
* **Prior Art (`yarima18`):** Relied on `gl.vm.run_nondet_unsafe`, which bypasses GenVM sandbox isolation and is discouraged in production.
* **This Implementation:** Uses standard `gl.vm.run_nondet(leader_fn, validator_fn)`, ensuring safe sandboxed execution in accordance with GenLayer Rule #7.

### 3. Dual-Format Dict/String LLM Response Handling
* **Prior Art (`yarima18`):** Assumed LLM output from `exec_prompt(..., response_format="json")` is always a raw JSON string and ran `json.loads(str(resp))`. On live GenVM nodes where `exec_prompt` returns a Python dictionary, `str(dict)` creates single-quoted string representations that cause `json.decoder.JSONDecodeError`, forcing contracts into fail-closed error states.
* **This Implementation:** Dynamically inspects response types (`isinstance(raw_response, dict)` vs string), ensuring seamless compatibility across mock unit tests and live validator nodes.

### 4. LLM Prompt Hardening Against Web Scrape Clutter
* **Prior Art (`yarima18`):** Passed raw web text directly to the model without explicit instructions to filter out boilerplate markup.
* **This Implementation:** Adds explicit prompt directives instructing the model to discard truncated HTML, CSS, JavaScript, and navigation menus, focusing strictly on journalistic factual reporting.

### 5. Concurrency & State Double-Write Safety
* **Prior Art (`yarima18`):** Only verified ID non-existence before the long non-deterministic execution started, leaving a race condition window if another transaction resolved the same event concurrently.
* **This Implementation:** Re-verifies state integrity immediately prior to the storage mutation (`self.events[clean_id] = record`), raising `gl.vm.UserError("Concurrent execution detected: Event has been resolved during validation")` if a collision occurs.

### 6. Live Studionet Consensus Verification
* **Prior Art (`yarima18`):** Only tested in local simulation.
* **This Implementation:** Deployed and actively verified on `studionet` with real on-chain transaction hashes across all canonical verdict states (`HAPPENED`, `NOT_HAPPENED`, and `UNRESOLVED`).
