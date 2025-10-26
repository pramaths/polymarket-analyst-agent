from hyperon import MeTTa
from typing import List, Dict, Any

def recommend_markets(all_markets: List[Dict[str, Any]], target_slug: str) -> List[str]:
    """
    Uses a MeTTa AtomSpace to recommend markets that are in the same category
    and share at least one tag with the target market.
    """
    metta = MeTTa()
    knowledge = []

    # --- Step 1: Load Knowledge into the AtomSpace ---
    # We assert facts about each market's category and tags.
    for market in all_markets:
        slug = market.get('slug')
        category = market.get('category')
        tags = market.get('tags', [])
        
        if not slug or not category:
            continue
        
        knowledge.append(f'(= (category-of "{slug}") "{category}")')
        
        for tag in tags:
            tag_name = tag.get('name')
            if tag_name:
                knowledge.append(f'(has-tag "{slug}" "{tag_name}")')

    metta.run(" ".join(knowledge))

    # --- Step 2: Define the Reasoning Rules ---
    # These rules define our recommendation logic in MeTTa's symbolic language.
    rules = '''
        ; Rule 1: Two markets share a tag if there is a tag $t 
        ; that both market $m1 and market $m2 have.
        (= (shares-tag $m1 $m2)
           (match &self ( (has-tag $m1 $t) (has-tag $m2 $t) ) True)
        )

        ; Rule 2: A market $m2 is a good recommendation for $m1 if:
        ; a) They are not the same market (!= $m1 $m2)
        ; b) Their categories are the same (== (category-of $m1) (category-of $m2))
        ; c) They share at least one tag (shares-tag $m1 $m2)
        (= (is-recommendation $m1 $m2)
           (if (and (!= $m1 $m2)
                      (== (category-of $m1) (category-of $m2))
                      (shares-tag $m1 $m2))
               $m2
               ())
        )
    '''
    metta.run(rules)

    # --- Step 3: Execute the Query ---
    # Ask MeTTa for all recommendations for our target slug.
    query = f'!(is-recommendation "{target_slug}" $x)'
    
    try:
        result = metta.run(query)
        
        # The result is a nested list of atoms. We need to extract the symbols.
        recommendations = []
        if result and result[0]:
            for item in result[0]:
                # Each item might be a Symbol atom, we get its name.
                if hasattr(item, 'get_name'):
                    recommendations.append(item.get_name())
        
        return recommendations
    except Exception as e:
        print(f"Error during MeTTa reasoning: {e}")
        return []
