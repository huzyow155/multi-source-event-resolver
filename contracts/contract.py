# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class EventResolution:
    """
    Structured storage record containing the consensus resolution of an event.
    
    Fields:
    - id: Unique identifier for the event.
    - event_description: The statement or condition being verified.
    - url1: Primary news or evidence source URL.
    - url2: Secondary independent news or evidence source URL.
    - verdict: Consensus verdict: HAPPENED, NOT_HAPPENED, CONFLICTING_EVIDENCE, or UNRESOLVED.
    - confidence: Confidence level assessed by LLM: HIGH, MEDIUM, or LOW.
    - source1_status: Assessment of source 1: CONFIRMS, REFUTES, NEUTRAL, or UNAVAILABLE.
    - source2_status: Assessment of source 2: CONFIRMS, REFUTES, NEUTRAL, or UNAVAILABLE.
    - summary: Synthesized rationale and evidence summary.
    - resolver: Address of the account that triggered the resolution transaction.
    """
    id: str
    event_description: str
    url1: str
    url2: str
    verdict: str
    confidence: str
    source1_status: str
    source2_status: str
    summary: str
    resolver: Address


def get_domain(url: str) -> str:
    clean = url.replace("https://", "").replace("http://", "")
    domain = clean.split("/")[0]
    return domain.replace("www.", "")


class Contract(gl.Contract):
    """
    Multi-Source Event Resolver Primitive for GenLayer.
    
    This contract serves as a decentralized, subjective oracle primitive.
    It accepts a natural-language event description and two independent source URLs,
    fetches and renders both sources on-chain via GenLayer web rendering,
    analyzes the evidence using an LLM, and achieves consensus across validator
    nodes via GenLayer Equivalence Principle (Optimistic Democracy).
    
    Consensus Model:
    Validators independently fetch the web sources and query the LLM.
    The validator comparison function enforces semantic consensus by matching
    the core verdict (HAPPENED, NOT_HAPPENED, CONFLICTING_EVIDENCE, UNRESOLVED)
    while ignoring non-deterministic syntactic variations in the LLM reasoning text.
    """
    
    events: TreeMap[str, EventResolution]
    event_ids: DynArray[str]
    resolution_count: bigint

    def __init__(self):
        """
        Contract constructor.
        Note: Per GenVM specifications, TreeMap and DynArray storage collections
        are initialized automatically by the runtime. Only scalar storage fields
        are explicitly assigned here.
        """
        self.resolution_count = bigint(0)

    @gl.public.write
    def resolve_event(
        self,
        event_id: str,
        event_description: str,
        url1: str,
        url2: str
    ):
        """
        Resolves an event by cross-referencing two independent web sources.
        
        Parameters:
        - event_id: Unique identifier for this resolution claim.
        - event_description: Clear description of the event that is claimed to have occurred.
        - url1: URL of the first independent news/evidence source.
        - url2: URL of the second independent news/evidence source.
        
        Reverts if:
        - Input strings are empty or malformed.
        - URLs do not use http:// or https:// schemes.
        - Both URLs belong to the same root domain (two independent root domains required).
        - The event_id has already been resolved (preventing double claims / state overwrites).
        """
        # 1. Input validation & sanity checks (pure deterministic checks)
        clean_id = event_id.strip()
        if len(clean_id) == 0:
            raise gl.vm.UserError("event_id cannot be empty")

        if self.events.get(clean_id, None) is not None:
            raise gl.vm.UserError("Event with this ID has already been resolved")

        clean_desc = event_description.strip()
        if len(clean_desc) < 5:
            raise gl.vm.UserError("event_description must be at least 5 characters long")

        clean_url1 = url1.strip()
        clean_url2 = url2.strip()
        if len(clean_url1) == 0 or len(clean_url2) == 0:
            raise gl.vm.UserError("Both source URLs must be provided")

        if not (clean_url1.startswith("http://") or clean_url1.startswith("https://")):
            raise gl.vm.UserError("url1 must be a valid HTTP or HTTPS URL")

        if not (clean_url2.startswith("http://") or clean_url2.startswith("https://")):
            raise gl.vm.UserError("url2 must be a valid HTTP or HTTPS URL")

        if get_domain(clean_url1) == get_domain(clean_url2):
            raise gl.vm.UserError("url1 and url2 must belong to different independent root domains")

        # 2. Capture parameters for non-deterministic execution
        # CRITICAL: Do NOT access self or storage inside leader_fn or validator_fn.
        captured_desc = clean_desc
        captured_url1 = clean_url1
        captured_url2 = clean_url2

        def execute_cross_check() -> dict:
            """
            Inner non-deterministic routine.
            Fetches web content and invokes LLM prompt with strict JSON schema.
            """
            # Fetch Source 1
            try:
                raw_text1 = gl.nondet.web.render(captured_url1, mode='text')
            except Exception:
                raw_text1 = "ERROR: Unable to render content from Source 1."

            # Fetch Source 2
            try:
                raw_text2 = gl.nondet.web.render(captured_url2, mode='text')
            except Exception:
                raw_text2 = "ERROR: Unable to render content from Source 2."

            # Truncate and sanitize content to avoid prompt overflow and escape breaks
            snippet1 = str(raw_text1)[:3000].replace('"', "'")
            snippet2 = str(raw_text2)[:3000].replace('"', "'")

            # Structured Prompt instructing deterministic classification
            prompt = f"""You are an objective, decentralized truth oracle and event resolution engine.
Your task is to verify whether the following real-world event has occurred by cross-checking two independent news sources.

EVENT TO VERIFY:
"{captured_desc}"

SOURCE 1 (URL: {captured_url1}):
[START SOURCE 1]
{snippet1}
[END SOURCE 1]

SOURCE 2 (URL: {captured_url2}):
[START SOURCE 2]
{snippet2}
[END SOURCE 2]

RESOLUTION RULES:
CRITICAL: The provided source text is heavily truncated and may contain raw HTML tags, CSS, JavaScript, or navigation menus. You must completely ignore all code, formatting tags, and navigational text. Focus ONLY on the journalistic sentences and factual reporting within the text.

1. Assess each source independently:
   - CONFIRMS: The source clearly reports the event happened as described.
   - REFUTES: The source explicitly contradicts the event, reports it did not happen, or was canceled.
   - NEUTRAL: The source does not mention the event, is irrelevant, or remains uncommitted.
   - UNAVAILABLE: The source content failed to load or is inaccessible.

2. Determine the synthesized verdict:
   - "HAPPENED": Both sources CONFIRM the event, OR one source CONFIRMS while the other is NEUTRAL without contradiction.
   - "NOT_HAPPENED": Both sources REFUTE the event, OR one source REFUTES while the other is NEUTRAL.
   - "CONFLICTING_EVIDENCE": One source CONFIRMS while the other source REFUTES the event.
   - "UNRESOLVED": Both sources are NEUTRAL or UNAVAILABLE, providing insufficient factual evidence to reach a conclusion.

3. Output format:
   You MUST respond with valid JSON only. Do not include markdown tags, greetings, or text outside the JSON object.
   Use this exact schema:
   {{
       "verdict": "HAPPENED" | "NOT_HAPPENED" | "CONFLICTING_EVIDENCE" | "UNRESOLVED",
       "confidence": "HIGH" | "MEDIUM" | "LOW",
       "source1_status": "CONFIRMS" | "REFUTES" | "NEUTRAL" | "UNAVAILABLE",
       "source2_status": "CONFIRMS" | "REFUTES" | "NEUTRAL" | "UNAVAILABLE",
       "summary": "Concise 1-2 sentence explanation of the finding."
   }}
"""

            try:
                raw_response = gl.nondet.exec_prompt(prompt, response_format="json")
                cleaned = str(raw_response).strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)

                # Normalize and validate verdict
                raw_verdict = str(parsed.get("verdict", "")).strip().upper()
                valid_verdicts = ("HAPPENED", "NOT_HAPPENED", "CONFLICTING_EVIDENCE", "UNRESOLVED")
                if raw_verdict in valid_verdicts:
                    final_verdict = raw_verdict
                else:
                    final_verdict = "UNRESOLVED"

                # Normalize confidence
                raw_conf = str(parsed.get("confidence", "LOW")).strip().upper()
                if raw_conf in ("HIGH", "MEDIUM", "LOW"):
                    final_conf = raw_conf
                else:
                    final_conf = "LOW"

                # Normalize source statuses
                valid_statuses = ("CONFIRMS", "REFUTES", "NEUTRAL", "UNAVAILABLE")
                s1_stat = str(parsed.get("source1_status", "UNAVAILABLE")).strip().upper()
                if s1_stat not in valid_statuses:
                    s1_stat = "UNAVAILABLE"

                s2_stat = str(parsed.get("source2_status", "UNAVAILABLE")).strip().upper()
                if s2_stat not in valid_statuses:
                    s2_stat = "UNAVAILABLE"

                summary_text = str(parsed.get("summary", "Resolution completed.")).strip()
                if len(summary_text) == 0:
                    summary_text = "No summary provided by oracle."

                return {
                    "verdict": final_verdict,
                    "confidence": final_conf,
                    "source1_status": s1_stat,
                    "source2_status": s2_stat,
                    "summary": summary_text
                }
            except Exception:
                # Fail-closed state: on any parser or communication error, return UNRESOLVED
                return {
                    "verdict": "UNRESOLVED",
                    "confidence": "LOW",
                    "source1_status": "UNAVAILABLE",
                    "source2_status": "UNAVAILABLE",
                    "summary": "Automated resolution failed due to content parsing error."
                }

        # 3. Leader and Validator functions for Optimistic Democracy consensus
        def leader_fn() -> dict:
            return execute_cross_check()

        def validator_fn(leaders_res) -> bool:
            """
            Validator node verification logic.
            Enforces semantic equivalence on the verdict. Minor variations in
            LLM wording or summary phrasing are deliberately disregarded to prevent
            consensus stalls, while ensuring the factual verdict is agreed upon.
            """
            if not isinstance(leaders_res, gl.vm.Return):
                return False

            leader_data = leaders_res.calldata
            if not isinstance(leader_data, dict):
                return False

            leader_verdict = leader_data.get("verdict")
            if not leader_verdict:
                return False

            # Validator independently performs web render and LLM assessment
            my_data = execute_cross_check()
            my_verdict = my_data.get("verdict")

            # Semantic match on the core verdict
            return my_verdict == leader_verdict

        # 4. Execute non-deterministic consensus via GenVM
        resolution_result = gl.vm.run_nondet(leader_fn, validator_fn)

        # 5. Commit verified resolution to persistent storage
        caller = gl.message.sender_address

        record = EventResolution(
            id=clean_id,
            event_description=clean_desc,
            url1=clean_url1,
            url2=clean_url2,
            verdict=str(resolution_result["verdict"]),
            confidence=str(resolution_result["confidence"]),
            source1_status=str(resolution_result["source1_status"]),
            source2_status=str(resolution_result["source2_status"]),
            summary=str(resolution_result["summary"]),
            resolver=caller
        )

        if self.events.get(clean_id, None) is not None:
            raise gl.vm.UserError("Concurrent execution detected: Event has been resolved during validation")

        self.events[clean_id] = record
        self.event_ids.append(clean_id)
        self.resolution_count += bigint(1)

    @gl.public.view
    def get_event(self, event_id: str) -> EventResolution:
        """
        Retrieves the resolution record for a given event ID.
        Reverts if the event has not been resolved.
        """
        clean_id = event_id.strip()
        record = self.events.get(clean_id, None)
        if record is None:
            raise gl.vm.UserError("Event ID not found")
        return record

    @gl.public.view
    def has_event(self, event_id: str) -> bool:
        """
        Checks whether an event with the given ID has already been resolved.
        """
        clean_id = event_id.strip()
        return self.events.get(clean_id, None) is not None

    @gl.public.view
    def get_event_count(self) -> bigint:
        """
        Returns the total number of events resolved by this contract.
        """
        return self.resolution_count

    @gl.public.view
    def get_event_id_at(self, index: bigint) -> str:
        """
        Returns the event ID at a specific index in the resolution log.
        Useful for off-chain indexing and paginated inspection.
        """
        idx = int(index)
        if idx < 0 or idx >= len(self.event_ids):
            raise gl.vm.UserError("Index out of bounds")
        return self.event_ids[idx]

    @gl.public.view
    def get_latest_event(self) -> EventResolution:
        """
        Returns the most recently resolved event record.
        Reverts if no events have been resolved yet.
        """
        if self.resolution_count == bigint(0):
            raise gl.vm.UserError("No events resolved yet")
        latest_idx = len(self.event_ids) - 1
        latest_id = self.event_ids[latest_idx]
        return self.events[latest_id]
