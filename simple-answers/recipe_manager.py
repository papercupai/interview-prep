"""
4. Recipe manager: simplest timed-test answer

- Store each recipe as its LIST OF VERSIONS. The current recipe is versions[-1], so Level 4 history costs nothing extra, and update is just an append.
- Find a name conflict with a plain scan (_taken) instead of keeping a name index in sync. There is nothing to update on rename or delete, so there is nothing to forget.
- edit = "known user" AND update. rollback = look up the old version, then edit with it, so the conflict check and version append are reused, not rewritten.
- Store and return copies of ingredient lists (list(...)), so a caller mutating its list can't change your stored data.
- No defaultdict here, on purpose: "rid in self.recipes" is how you tell whether a recipe exists, and a defaultdict would create an empty recipe the first time you read a missing id.
"""


class RecipeManager:
    def __init__(self):
        self.recipes = {}  # id -> [(name, ingredients), ...]   every version, newest last
        self.next_id = 1
        self.users = set()

    def _taken(self, name, other_than=None):  # case-insensitive name conflict
        for rid, versions in self.recipes.items():
            if rid != other_than and versions[-1][0].lower() == name.lower():
                return True
        return False

    # Level 1
    def create(self, name, ingredients):
        if self._taken(name):
            return None
        rid = self.next_id
        self.next_id += 1  # ids are never reused
        self.recipes[rid] = [(name, list(ingredients))]
        return rid

    def get(self, rid):
        if rid not in self.recipes:
            return None
        name, ingredients = self.recipes[rid][-1]
        return (name, list(ingredients))

    def update(self, rid, name, ingredients):
        if rid not in self.recipes or self._taken(name, rid):
            return False
        self.recipes[rid].append((name, list(ingredients)))
        return True

    def delete(self, rid):
        if rid not in self.recipes:
            return False
        del self.recipes[rid]  # frees the name
        return True

    # Level 2
    def search(self, text):
        hits = []
        for rid, versions in self.recipes.items():
            if text.lower() in versions[-1][0].lower():
                hits.append(rid)
        hits.sort(key=lambda rid: (len(self.recipes[rid][-1][1]), rid))  # fewest ingredients, then id
        return hits

    # Level 3
    def add_user(self, user_id):
        if user_id in self.users:
            return False
        self.users.add(user_id)
        return True

    def edit(self, user_id, rid, name, ingredients):
        if user_id not in self.users:
            return False
        return self.update(rid, name, ingredients)

    # Level 4
    def versions(self, rid):
        result = []
        for name, ingredients in self.recipes.get(rid, []):
            result.append((name, list(ingredients)))
        return result

    def rollback(self, user_id, rid, version):
        if rid not in self.recipes or not 1 <= version <= len(self.recipes[rid]):
            return False
        name, ingredients = self.recipes[rid][version - 1]
        return self.edit(user_id, rid, name, ingredients)  # conflict check + new version for free


# ---- tests: python3 recipe_manager.py ----
if __name__ == "__main__":
    r = RecipeManager()
    # Level 1: the page's "check yourself"
    assert r.create("Soup", ["water", "salt"]) == 1
    assert r.create("sOUp", []) is None
    assert r.get(1) == ("Soup", ["water", "salt"]) and r.get(9) is None
    assert r.create("Cake", ["flour", "egg", "sugar"]) == 2
    assert r.update(2, "SOUP", []) is False                  # conflicts with recipe 1
    assert r.update(1, "SOUP", ["water", "salt"]) is True    # renaming yourself is fine
    assert r.update(9, "x", []) is False
    assert r.delete(1) is True and r.delete(1) is False
    assert r.create("soup", ["water"]) == 3                  # name freed, id not reused
    # Level 2
    r.create("Soup dumplings", ["flour", "pork"])            # id 4
    assert r.search("SOUP") == [3, 4]                        # 1 ingredient, then 2
    assert r.search("") == [3, 4, 2]
    assert r.search("zzz") == []
    # Level 3
    assert r.add_user("ann") is True and r.add_user("ann") is False
    assert r.edit("bob", 3, "Broth", []) is False            # unknown user
    assert r.edit("ann", 3, "Cake", []) is False             # conflicting name
    assert r.get(3) == ("soup", ["water"])                   # nothing changed
    # Level 4: edit to "Stew", roll back to version 1 -> version 3 named "Soup"
    s = RecipeManager()
    s.add_user("ann")
    assert s.create("Soup", ["water", "salt"]) == 1
    assert s.edit("ann", 1, "Stew", ["beef"]) is True
    assert s.rollback("ann", 1, 1) is True
    assert s.versions(1) == [("Soup", ["water", "salt"]), ("Stew", ["beef"]), ("Soup", ["water", "salt"])]
    assert s.get(1) == ("Soup", ["water", "salt"])
    assert s.rollback("ann", 1, 0) is False and s.rollback("ann", 1, 4) is False
    assert s.rollback("bob", 1, 2) is False and s.rollback("ann", 9, 1) is False
    assert s.edit("ann", 1, "Broth", []) is True             # frees "Soup"...
    assert s.create("soup", []) == 2                         # ...which recipe 2 takes
    assert s.rollback("ann", 1, 1) is False                  # old name now belongs to recipe 2
    assert len(s.versions(1)) == 4 and s.versions(9) == []
    print("recipe_manager: all checks passed")
