"""Append-before-archive updates, with a durable journal for interrupted writes."""
import json
from pathlib import Path

from publishing.config import atomic_write


def replace_blocks(page_id, blocks, properties, request, list_children, state_dir):
    journal = Path(state_dir) / f"{page_id}.json"
    if journal.exists():
        raise RuntimeError(f'上次同步未完成。请先按日志核对/恢复 Notion 内容，再移走日志后重试: {journal}')
    state = {'page_id': page_id, 'old_ids': [b['id'] for b in list_children(page_id)],
             'new_ids': [], 'archive_attempts': [], 'append_pending': False}

    def save():
        atomic_write(journal, json.dumps(state, ensure_ascii=False, indent=2))

    journal.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents two local synchronizers from sharing a journal.
    with journal.open('x', encoding='utf-8') as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    try:
        for offset in range(0, len(blocks), 100):
            batch = blocks[offset:offset + 100]
            state['append_pending'] = True
            save()
            try:
                response = request('patch', f'/blocks/{page_id}/children', json_data={'children': batch})
            except Exception as exc:
                status = getattr(getattr(exc, 'response', None), 'status_code', None)
                if status in {400, 401, 403, 404, 409, 429}:
                    state['append_pending'] = False  # Explicit rejection, not an ambiguous timeout.
                    save()
                raise
            created = response.get('results', [])
            state['new_ids'].extend(b['id'] for b in created)
            if len(created) != len(batch):
                save()
                raise RuntimeError('Notion 未确认全部新增 blocks；保留旧正文并停止同步')
            state['append_pending'] = False
            save()
        # New content is complete before any old content is archived.
        for block_id in state['old_ids']:
            state['archive_attempts'].append(block_id)
            save()
            request('patch', f'/blocks/{block_id}', json_data={'archived': True})
        request('patch', f'/pages/{page_id}', json_data={'properties': properties})
    except Exception:
        recovery_errors = []
        for block_id in state['archive_attempts']:
            try:
                request('patch', f'/blocks/{block_id}', json_data={'archived': False})
            except Exception as exc:
                recovery_errors.append(str(exc))
        # Never remove the replacement until restoration of the original succeeded.
        if not recovery_errors:
            for block_id in state['new_ids']:
                try:
                    request('patch', f'/blocks/{block_id}', json_data={'archived': True})
                except Exception as exc:
                    recovery_errors.append(str(exc))
        if recovery_errors or state['append_pending']:
            state['recovery_errors'] = recovery_errors
            save()
            print(f'[ERR] 需要核对中断的同步，恢复日志: {journal}')
        else:
            journal.unlink()
        raise
    journal.unlink()
