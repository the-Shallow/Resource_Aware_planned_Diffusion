"""Synthetic CPU checks for the stage layout produced by the upstream parser."""

import pytest
import torch

from dream.control_tags import (
    ASYNC_END,
    ASYNC_START,
    MASK_TOKEN_ID,
    PROMISE_END,
    PROMISE_START,
    SYNC_TOKEN_ID,
)
from dream.pd_utils import create_pd_inputs


def make_stage(*tokens: int, length_scale: float | None = None):
    prefix = torch.tensor([tokens], dtype=torch.long)
    prefix_attention = torch.ones((1, len(tokens), len(tokens)), dtype=torch.bool)
    return create_pd_inputs(
        input_ids=prefix,
        prev_attention_mask=prefix_attention,
        device=prefix.device,
        length_scale=length_scale,
    )


def test_two_promises_have_absolute_exclusive_boundaries_and_isolated_masks():
    # Dream digit token IDs 17 and 20 represent 2 and 5, respectively.
    prefix = (42, PROMISE_START, 101, 17, PROMISE_END,
              PROMISE_START, 102, 20, PROMISE_END)
    full_sequence, attention_mask, count, block_info = make_stage(*prefix)

    assert count == 2
    assert block_info == [(9, 31, 20), (31, 83, 50)]
    assert full_sequence.shape == (1, 83)
    assert torch.equal(full_sequence[0, :9], torch.tensor(prefix))
    assert (full_sequence == MASK_TOKEN_ID).sum().item() == 70

    for start, end, content_length in block_info:
        assert end - start == content_length + 2
        assert full_sequence[0, start].item() == ASYNC_START
        assert full_sequence[0, end - 1].item() == ASYNC_END
        assert torch.all(full_sequence[0, start + 1:end - 1] == MASK_TOKEN_ID)

    # Both blocks see the common prefix, but not each other's interior.
    assert attention_mask[0, 10, 0].item()
    assert attention_mask[0, 32, 0].item()
    assert not attention_mask[0, 10, 32].item()
    assert not attention_mask[0, 32, 10].item()


def test_two_digit_promise_uses_length_scale():
    # 17, 18 encode the two-digit number 23; a scale of 2 creates 46 masks.
    _, _, count, block_info = make_stage(
        42, PROMISE_START, 101, 17, 18, PROMISE_END, length_scale=2
    )
    assert count == 1
    assert block_info == [(6, 54, 46)]


def test_only_promises_after_latest_sync_form_the_next_stage():
    _, _, count, block_info = make_stage(
        42, PROMISE_START, 101, 17, PROMISE_END,
        SYNC_TOKEN_ID,
        43, PROMISE_START, 102, 20, PROMISE_END,
    )
    assert count == 1
    assert block_info == [(11, 63, 50)]


def test_promise_without_a_number_is_rejected():
    with pytest.raises(ValueError, match="No number found in promise"):
        make_stage(42, PROMISE_START, 101, PROMISE_END)
