"""
7. Course registration: simplest timed-test answer

- Two defaultdicts do all the work. enrolled[course] is the set of students in it right now, and hist[(course, student)] is a list of (time, grade) entries. Neither needs an "if missing, create" line.
- register, drop and set_grade each append one entry to hist. Register and drop append (time, None), which means "enrolled but ungraded" or "not enrolled"; the spec answers None for both, so one list covers both. A grade appends (time, grade).
- The current grade is the last entry in hist. A re-registration appends (time, None), so an old grade never carries over.
- grade_at walks hist backwards and returns the first entry at or before `at`. It's the same look-back loop as the KV database and the bank, with no Registration class and no binary search.
- roster: build the graded list and the ungraded list separately, then concatenate. It's easier to get right than one clever sort key with None in it.
- Level 3/4 add `now` as a LAST parameter with default 0, so the Level 2 calls keep working unchanged.
"""

from collections import defaultdict


class CourseRegistration:
    def __init__(self):
        self.cap = {}                     # course_id -> capacity (None = no limit); a course exists iff it is here
        self.students = set()
        self.enrolled = defaultdict(set)  # course_id -> students enrolled right now
        self.hist = defaultdict(list)     # (course_id, student_id) -> [(time, grade or None)]

    def _grade(self, cid, sid):  # current grade, or None
        return self.hist[cid, sid][-1][1]

    # Level 1
    def add_course(self, cid):
        if cid in self.cap:
            return False
        self.cap[cid] = None
        return True

    def add_student(self, sid):
        if sid in self.students:
            return False
        self.students.add(sid)
        return True

    def has_course(self, cid):
        return cid in self.cap

    def has_student(self, sid):
        return sid in self.students

    # Level 2 (Level 3/4 add `now`; Level 2 calls default it to 0)
    def register(self, cid, sid, now=0):
        if cid not in self.cap or sid not in self.students or sid in self.enrolled[cid]:
            return False
        if self.cap[cid] is not None and len(self.enrolled[cid]) >= self.cap[cid]:
            return False
        self.enrolled[cid].add(sid)
        self.hist[cid, sid].append((now, None))  # enrolled, no grade yet
        return True

    def set_grade(self, cid, sid, grade, now=0):
        if sid not in self.enrolled[cid]:
            return False
        self.hist[cid, sid].append((now, grade))
        return True

    def roster(self, cid):
        graded, ungraded = [], []
        for sid in self.enrolled[cid]:  # unknown course: an empty set
            if self._grade(cid, sid) is None:
                ungraded.append(sid)
            else:
                graded.append(sid)
        graded.sort(key=lambda sid: (-self._grade(cid, sid), sid))
        ungraded.sort()
        return graded + ungraded

    # Level 3
    def set_capacity(self, cid, limit):
        if cid not in self.cap or limit < 0:
            return False
        self.cap[cid] = limit
        return True

    def drop(self, cid, sid, now=0):
        if sid not in self.enrolled[cid]:
            return False
        self.enrolled[cid].remove(sid)  # frees the seat immediately
        self.hist[cid, sid].append((now, None))
        return True

    # Level 4
    def grade_at(self, cid, sid, at):
        for t, grade in reversed(self.hist[cid, sid]):
            if t <= at:
                return grade
        return None


# ---- tests: python3 course_registration.py ----
if __name__ == "__main__":
    cr = CourseRegistration()
    # Level 1
    assert cr.add_course("CS1") is True and cr.add_course("CS1") is False
    assert cr.add_student("amy") is True and cr.add_student("ben") is True and cr.add_student("amy") is False
    assert cr.has_course("CS1") and not cr.has_course("CS9")
    assert cr.has_student("ben") and not cr.has_student("zed")
    # Level 2: the page's "check yourself"
    assert cr.register("CS1", "amy") is True and cr.register("CS1", "ben") is True
    assert cr.register("CS1", "amy") is False                            # duplicate
    assert cr.register("CS9", "amy") is False and cr.register("CS1", "zed") is False
    assert cr.set_grade("CS1", "ben", 90) is True
    assert cr.roster("CS1") == ["ben", "amy"]
    assert cr.set_grade("CS1", "zed", 50) is False and cr.roster("CS9") == []
    assert not cr.has_course("CS9")                                      # reading enrolled["CS9"] did not create a course
    cr.add_student("cat"); cr.add_student("dan"); cr.register("CS1", "cat"); cr.register("CS1", "dan")
    cr.set_grade("CS1", "dan", 90); cr.set_grade("CS1", "amy", 70)
    assert cr.roster("CS1") == ["ben", "dan", "amy", "cat"]               # grade desc, id asc, ungraded last
    # Level 3: with capacity 1, dropping ben frees a seat for amy
    cr.add_course("CS2")
    assert cr.set_capacity("CS2", -1) is False and cr.set_capacity("CS9", 1) is False
    assert cr.set_capacity("CS2", 1) is True
    assert cr.register("CS2", "ben", 1) is True
    assert cr.register("CS2", "amy", 2) is False                         # full
    assert cr.drop("CS2", "amy", 3) is False                             # not enrolled
    assert cr.drop("CS2", "ben", 3) is True
    assert cr.register("CS2", "amy", 3) is True
    assert cr.roster("CS2") == ["amy"]
    assert cr.set_capacity("CS2", 0) is True and cr.register("CS2", "cat", 4) is False
    # Level 4: grade look-back across a drop and a re-registration
    g = CourseRegistration()
    g.add_course("C"); g.add_student("s")
    g.register("C", "s", 10)
    assert g.grade_at("C", "s", 9) is None                               # before enrollment
    assert g.grade_at("C", "s", 11) is None                              # before the first grade
    g.set_grade("C", "s", 80, 12); g.set_grade("C", "s", 85, 20)
    assert g.grade_at("C", "s", 12) == 80 and g.grade_at("C", "s", 19) == 80
    assert g.grade_at("C", "s", 20) == 85 and g.grade_at("C", "s", 29) == 85
    g.drop("C", "s", 30)
    assert g.grade_at("C", "s", 30) is None and g.grade_at("C", "s", 35) is None   # after dropping
    g.register("C", "s", 40)
    assert g.grade_at("C", "s", 40) is None                              # new registration, ungraded
    assert g.roster("C") == ["s"]                                        # the old grade did not carry over
    g.set_grade("C", "s", 70, 45)
    assert g.grade_at("C", "s", 50) == 70 and g.grade_at("C", "s", 25) == 85
    assert g.grade_at("C", "nobody", 50) is None and g.grade_at("X", "s", 50) is None
    print("course_registration: all checks passed")
