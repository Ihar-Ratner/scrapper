import re
from typing import Tuple, List

def validate_article_ids(article_ids: List[str]) -> Tuple[List[str], List[str]]:
    valid_ids = []
    invalid_ids = []
    
    for aid in article_ids:
        if re.match(r'^\d+$', aid.strip()):
            valid_ids.append(aid.strip())
        else:
            invalid_ids.append(aid)
    
    return valid_ids, invalid_ids
