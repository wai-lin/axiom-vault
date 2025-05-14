from ipv8.messaging.payload_dataclass import dataclass
import hashlib
import json
import os
from typing import Tuple, Optional


@dataclass(msg_id=5)
class CommitReveal:
    """
    Commit-reveal scheme for lottery number generation
    
    Attributes:
        validator_id: ID of the validator peer
        commit_hash: Hash of the committed random value and salt
        reveal_value: The revealed random value (0-99)
        salt: Random salt used in the commit
    """
    validator_id: str
    commit_hash: Optional[str] = None
    reveal_value: Optional[int] = None
    salt: Optional[str] = None

    def generate_commit(self, random_value: int) -> Tuple[str, str]:
        """
        Generate a commit hash for a random value with a random salt
        
        Args:
            random_value: The random value to commit (0-99)
            
        Returns:
            Tuple[str, str]: (commit_hash, salt)
        """
        self.reveal_value = random_value
        self.salt = hashlib.sha256(os.urandom(32)).hexdigest()[:16]

        commit_string = f"{random_value}{self.salt}".encode()
        self.commit_hash = hashlib.sha256(commit_string).hexdigest()

        return self.commit_hash, self.salt

    def verify_reveal(self, revealed_value: int, salt: str) -> bool:
        """
        Verify that a revealed value matches the previously committed hash
        
        Args:
            revealed_value: The revealed random value
            salt: The salt used in the commit
            
        Returns:
            bool: True if the reveal is valid, False otherwise
        """
        if not self.commit_hash:
            return False

        verify_string = f"{revealed_value}{salt}".encode()
        verify_hash = hashlib.sha256(verify_string).hexdigest()

        return verify_hash == self.commit_hash

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization
        
        Returns:
            dict: CommitReveal data as dictionary
        """
        return {
            "validator_id": self.validator_id,
            "commit_hash": self.commit_hash,
            "reveal_value": self.reveal_value,
            "salt": self.salt
        }

    def to_bytes(self) -> bytes:
        """
        Convert to bytes for inclusion in a block
        
        Returns:
            bytes: Serialized CommitReveal data
        """
        return json.dumps(self.to_dict()).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> 'CommitReveal':
        """
        Create a CommitReveal object from bytes
        
        Args:
            data: Serialized CommitReveal data
            
        Returns:
            CommitReveal: Deserialized CommitReveal object
        """
        commit_dict = json.loads(data.decode())
        return cls(
            validator_id=commit_dict["validator_id"],
            commit_hash=commit_dict.get("commit_hash"),
            reveal_value=commit_dict.get("reveal_value"),
            salt=commit_dict.get("salt")
        )
