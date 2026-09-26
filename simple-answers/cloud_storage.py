"""
5. Cloud file storage: simplest timed-test answer

- One dict, name -> (size, owner). Level 1 files have owner None, which means "no capacity limit", so Level 3 is one extra field, not a second store.
- Compute a user's used space with a loop over files (_used) instead of keeping a counter in sync through add, copy, merge and restore.
- largest: sort the matching names with key=(-size, name), which gives "size descending, then name ascending" in one sort.
- Level 4 restore: check for collisions FIRST, then rebuild. Nothing is half-applied when you reject.
- Deleting from a dict while looping over it raises an error, so loop over a copy: list(self.files.items()).
- No defaultdict here: "name in self.files" and "user in self.capacity" are the existence checks, and a defaultdict read would silently create entries.
"""


class CloudStorage:
    def __init__(self):
        self.files = {}     # name -> (size, owner)   owner None = plain Level 1 file
        self.capacity = {}  # user_id -> capacity
        self.backups = {}   # user_id -> {name: size}

    def _used(self, user):
        total = 0
        for size, owner in self.files.values():
            if owner == user:
                total += size
        return total

    def _fits(self, user, size):
        return user is None or self._used(user) + size <= self.capacity[user]

    # Level 1
    def add_file(self, name, size):
        if name in self.files:
            return False
        self.files[name] = (size, None)
        return True

    def copy_file(self, source, destination):
        if source not in self.files or destination in self.files:
            return False
        size, owner = self.files[source]
        if not self._fits(owner, size):  # a copy keeps the owner and must fit
            return False
        self.files[destination] = (size, owner)
        return True

    def get_size(self, name):
        if name not in self.files:
            return None
        return self.files[name][0]

    # Level 2
    def largest(self, prefix, n):
        if n <= 0:
            return []
        names = []
        for name in self.files:
            if name.startswith(prefix):
                names.append(name)
        names.sort(key=lambda name: (-self.files[name][0], name))
        result = []
        for name in names[:n]:
            result.append(f"{name}({self.files[name][0]})")
        return result

    # Level 3
    def add_user(self, user, capacity):
        if user in self.capacity:
            return False
        self.capacity[user] = capacity
        return True

    def add_owned_file(self, user, name, size):
        if user not in self.capacity or name in self.files or not self._fits(user, size):
            return None
        self.files[name] = (size, user)
        return self.capacity[user] - self._used(user)

    # Level 4
    def merge_user(self, keep, remove):
        if keep == remove or keep not in self.capacity or remove not in self.capacity:
            return False
        for name, (size, owner) in list(self.files.items()):
            if owner == remove:
                self.files[name] = (size, keep)
        self.capacity[keep] += self.capacity.pop(remove)
        self.backups.pop(remove, None)
        return True

    def backup_user(self, user):
        if user not in self.capacity:
            return None
        saved = {}
        for name, (size, owner) in self.files.items():
            if owner == user:
                saved[name] = size
        self.backups[user] = saved
        return len(saved)

    def restore_user(self, user):
        saved = self.backups.get(user)
        if user not in self.capacity or saved is None:
            return None
        for name in saved:  # check EVERY collision before changing anything
            if name in self.files and self.files[name][1] != user:
                return None
        for name, (size, owner) in list(self.files.items()):  # a copy: we delete while looping
            if owner == user:
                del self.files[name]
        for name, size in saved.items():
            self.files[name] = (size, user)
        return len(saved)


# ---- tests: python3 cloud_storage.py ----
if __name__ == "__main__":
    c = CloudStorage()
    # Level 1
    assert c.add_file("a.txt", 8) is True and c.add_file("a.txt", 1) is False
    assert c.get_size("a.txt") == 8 and c.get_size("A.txt") is None   # case-sensitive
    assert c.copy_file("a.txt", "b.txt") is True and c.get_size("b.txt") == 8
    assert c.copy_file("zz", "y") is False and c.copy_file("a.txt", "b.txt") is False
    # Level 2: the page's "check yourself"
    c.add_file("c.txt", 12)
    assert c.largest("", 3) == ["c.txt(12)", "a.txt(8)", "b.txt(8)"]
    assert c.largest("", 1) == ["c.txt(12)"] and c.largest("a", 5) == ["a.txt(8)"]
    assert c.largest("", 0) == [] and c.largest("", -2) == []
    # Level 3: capacity 10 fits size 10 but not one more byte
    assert c.add_user("u", 10) is True and c.add_user("u", 99) is False
    assert c.add_owned_file("u", "u/big", 10) == 0
    assert c.add_owned_file("u", "u/one", 1) is None
    assert c.add_owned_file("nobody", "n/x", 1) is None
    assert c.copy_file("u/big", "u/big2") is False               # copy keeps owner, doesn't fit
    c.add_user("v", 20)
    assert c.add_owned_file("v", "v/a", 5) == 15
    assert c.copy_file("v/a", "v/b") is True and c.add_owned_file("v", "v/c", 1) == 9
    # Level 4
    assert c.merge_user("u", "u") is False and c.merge_user("u", "zz") is False
    assert c.merge_user("u", "v") is True
    assert c.add_owned_file("v", "v/d", 1) is None                # v is gone
    assert c.add_owned_file("u", "u/more", 9) == 0                # capacity 30, 21 used after the merge
    assert c.add_user("v", 3) is True                             # the removed id can come back
    # backup / restore
    d = CloudStorage()
    d.add_user("x", 100); d.add_user("y", 100)
    d.add_owned_file("x", "x/1", 5); d.add_owned_file("x", "x/2", 5)
    assert d.restore_user("x") is None                            # no backup yet
    assert d.backup_user("x") == 2 and d.backup_user("zz") is None
    d.add_owned_file("x", "x/3", 5)
    assert d.restore_user("x") == 2                               # back to the saved two files
    assert d.get_size("x/3") is None and d.get_size("x/1") == 5
    assert d.add_owned_file("x", "x/3", 90) == 0                  # restored usage is 10
    # There is no delete method, so simulate another user now holding a saved name.
    d.backup_user("x")
    d.files["x/1"] = (5, "y")
    before = dict(d.files)
    assert d.restore_user("x") is None                            # collision: rejected...
    assert d.files == before                                      # ...and nothing changed
    print("cloud_storage: all checks passed")
