
from final_project.messages.block import Block


def calculate_block_hash(block: Block):
    block_string = json.dumps(
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "winning_number": block.winning_number,
            "commit_reveals": block.commit_reveals,
            "validator": block.validator,
        },
        sort_keys=True,
    ).encode()
    hash_string = hashlib.sha256(block_string).hexdigest()
    block.hash = hash_string