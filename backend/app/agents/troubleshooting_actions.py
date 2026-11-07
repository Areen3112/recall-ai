"""Conservative recognition of a small set of troubleshooting actions.

This is deliberately not a general semantic parser. Unknown or ambiguous actions
are left for human review instead of being silently treated as validated.
"""

from __future__ import annotations

import re

BLUETOOTH_REPAIR_ACTION = "bluetooth_forget_and_pair"

_PAIR_ACTION = re.compile(
    r"\b(?:pair|pairing|re-pair|re-pairing|connect|reconnect|setup|set up|discovery)\b", re.I
)
_REMOVE_ACTION = re.compile(
    r"\b(?:forget|forgetting|remove|removing|delete|deleting|clear|clearing|erase|erasing|unpair|unpairing)\b", re.I
)
_DEVICE_CONTEXT = re.compile(r"\b(?:bluetooth|headphones?|headsets?|earbuds?|paired devices?|saved profiles?)\b", re.I)
_DEVICE_REFERENCE = re.compile(
    r"\b(?:bluetooth|headphones?|headsets?|earbuds?|paired devices?|saved profiles?|devices?)\b", re.I
)
_ACTION_CUE = re.compile(r"\b(?:try|recommend|suggest|should|could|can|please|step|first)\b", re.I)
_DIRECTIVE_START = re.compile(
    r"^\s*(?:find|locate|select|choose|tap|click|forget|remove|delete|clear|erase|unpair|"
    r"put|place|enter|start|begin|pair|re-pair|connect|reconnect)\b",
    re.I,
)
_NEGATED_INSTRUCTION = re.compile(r"\b(?:do not|don't|never|avoid|should not|shouldn't)\b", re.I)
_ATTEMPT = re.compile(r"\b(?:i|we)\s+(?:have\s+)?(?:tried|followed|attempted|tested)\b", re.I)
_FAILURE = re.compile(r"\b(?:did not|didn't|does not|doesn't)\s+(?:help|work|resolve)\b|\bfailed\b", re.I)
_REFERENTIAL_FAILURE = re.compile(
    r"^\s*(?:it|that|this|the step)\s+(?:did not|didn't|does not|doesn't)\s+(?:help|work|resolve)\b",
    re.I,
)
_AMBIGUOUS_BLUETOOTH_ADVICE = re.compile(
    r"\b(?:bluetooth|headphones?|headsets?|earbuds?)\b.{0,100}"
    r"\b(?:fresh setup|start over|start from scratch|new pairing|pair from scratch|reconfigure)\b"
    r"|\b(?:fresh setup|start over|start from scratch|new pairing|pair from scratch|reconfigure)\b.{0,100}"
    r"\b(?:bluetooth|headphones?|headsets?|earbuds?)\b",
    re.I,
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|[\n;]+")


def mentions_bluetooth_repair_action(text: str) -> bool:
    return bool(_DEVICE_CONTEXT.search(text) and _PAIR_ACTION.search(text) and _REMOVE_ACTION.search(text))


def recommended_action_ids(text: str) -> set[str]:
    """Identify explicit recommendations for the known Bluetooth repair action."""
    action_ids: set[str] = set()
    sentences = _SENTENCE_SPLIT.split(text)
    for sentence in sentences:
        if not mentions_bluetooth_repair_action(sentence):
            continue
        if _ACTION_CUE.search(sentence) or _DIRECTIVE_START.search(sentence) or re.match(
            r"^\s*(?:forget|remove|delete|clear|erase|unpair|pair|re-pair)\b", sentence, re.I
        ):
            if not re.search(r"\b(?:do not|don't|avoid|never)\b", sentence, re.I):
                action_ids.add(BLUETOOTH_REPAIR_ACTION)

    # Support the same explicit action when an assistant gives it as sequential
    # steps. Keep the recognition bounded: require Bluetooth/device context in
    # the response, a directive to forget/remove the device, then a later pairing
    # directive within four sentences. Generic Bluetooth advice does not match.
    if not action_ids and _DEVICE_CONTEXT.search(text):
        for remove_index, sentence in enumerate(sentences):
            if (
                not _REMOVE_ACTION.search(sentence)
                or not _DEVICE_REFERENCE.search(sentence)
                or _NEGATED_INSTRUCTION.search(sentence)
                or not (_ACTION_CUE.search(sentence) or _DIRECTIVE_START.search(sentence))
            ):
                continue
            for pair_sentence in sentences[remove_index + 1 : remove_index + 6]:
                if (
                    _PAIR_ACTION.search(pair_sentence)
                    and not _NEGATED_INSTRUCTION.search(pair_sentence)
                    and (_ACTION_CUE.search(pair_sentence) or _DIRECTIVE_START.search(pair_sentence))
                ):
                    action_ids.add(BLUETOOTH_REPAIR_ACTION)
                    break
            if action_ids:
                break
    return action_ids


def explicitly_reported_failed_action_ids(text: str) -> set[str]:
    """Recognize a reported failure only when the customer names the action.

    A pronoun-only failure may refer to an action explicitly attempted in the
    immediately preceding sentence. No matches are made across arbitrary clauses.
    """
    sentences = _SENTENCE_SPLIT.split(text)
    for index, sentence in enumerate(sentences):
        if not _ATTEMPT.search(sentence) or not mentions_bluetooth_repair_action(sentence):
            continue
        if _FAILURE.search(sentence):
            # A contrast clause can describe a different action's failure.
            contrast = re.search(r"\b(?:but|however|whereas|although|though|while|instead)\b", sentence, re.I)
            if contrast:
                contrast_clause = sentence[contrast.end():]
                if not (
                    _REFERENTIAL_FAILURE.search(contrast_clause)
                    or (mentions_bluetooth_repair_action(contrast_clause) and _FAILURE.search(contrast_clause))
                ):
                    continue
            return {BLUETOOTH_REPAIR_ACTION}
        if index + 1 < len(sentences) and _REFERENTIAL_FAILURE.search(sentences[index + 1]):
            return {BLUETOOTH_REPAIR_ACTION}
    return set()


def failed_action_response_status(text: str, failed_action_ids: set[str]) -> str:
    """Return repeat, uncertain, or avoided for the known action taxonomy."""
    if not failed_action_ids:
        return "avoided"
    if BLUETOOTH_REPAIR_ACTION in failed_action_ids:
        if recommended_action_ids(text) & failed_action_ids:
            return "repeat"
        if _AMBIGUOUS_BLUETOOTH_ADVICE.search(text):
            return "uncertain"
    # Unknown structured action identifiers must never be treated as validated.
    if failed_action_ids - {BLUETOOTH_REPAIR_ACTION}:
        return "uncertain"
    return "avoided"
