from dataclasses import dataclass, field
from typing import List


@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    skills: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "skills": list(self.skills),
        }

    def __repr__(self) -> str:
        return (
            f"ResumeData(name={self.name!r}, email={self.email!r}, skills={self.skills!r})"
        )
