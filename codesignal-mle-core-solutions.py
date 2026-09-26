"""
CodeSignal "Machine Learning Engineering Core" — reference solutions + tests.

Pure Python 3, no numpy / sklearn (the assessment forbids libraries in Module 3).
Regions between `# >>> implement` and `# <<< implement` are what the practice file
blanks out; everything else is the kind of skeleton CodeSignal hands you.

Run:  python3 codesignal-mle-core-solutions.py      (prints PASS per section)
"""
import math
import random

# ==== module2_triple ====
# Module 2 sample (from CodeSignal's technical brief): count the words that contain
# some letter at least three times, case-insensitive.
def triple_duplicate_words(sentence):
    # >>> implement
    count = 0
    for word in sentence.split():
        w = word.lower()
        if any(w.count(ch) >= 3 for ch in set(w)):
            count += 1
    return count
    # <<< implement


# ==== module2_digits ====
# Variation: split a number into digits; return the sum of the even digits minus
# the sum of the odd digits. digit_balance(31724) -> (2 + 4) - (3 + 1 + 7) = -5
def digit_balance(n):
    # >>> implement
    even = odd = 0
    for ch in str(abs(n)):
        d = int(ch)
        if d % 2 == 0:
            even += d
        else:
            odd += d
    return even - odd
    # <<< implement


# ==== module2_two_arrays ====
# Variation (brief wording): from `a`, build `neg` (values < 0) and `pos` (values >= 0);
# reverse `neg`, then return neg + pos.   split_and_prepend([3, -1, 4, -5, 0]) -> [-5, -1, 3, 4, 0]
def split_and_prepend(a):
    # >>> implement
    neg = [x for x in a if x < 0]
    pos = [x for x in a if x >= 0]
    neg.reverse()
    return neg + pos
    # <<< implement


# ==== module2_strings ====
# Variation: reverse every word of length >= k in place, keep word order and spacing.
# reverse_long_words("the quick brown fox", 4) -> "the kciuq nworb fox"
def reverse_long_words(sentence, k):
    # >>> implement
    out = []
    for word in sentence.split(" "):
        out.append(word[::-1] if len(word) >= k else word)
    return " ".join(out)
    # <<< implement


# ==== module2_compare ====
# Variation: count pairs of words (i < j) that are anagrams of each other, case-insensitive.
# anagram_pairs("Listen silent enlist tinsel banana") -> 6  (4 anagrams -> C(4,2))
def anagram_pairs(sentence):
    # >>> implement
    keys = ["".join(sorted(w.lower())) for w in sentence.split()]
    pairs = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if keys[i] == keys[j]:
                pairs += 1
    return pairs
    # <<< implement


# ==== knn ====
# Module 3 sample (verbatim shape from the brief). Only euc_dist and k_neighbors are yours.
def euc_dist(value1, value2):
    # >>> implement
    return sum((a - b) ** 2 for a, b in zip(value1, value2)) ** 0.5
    # <<< implement

def k_neighbors(train_data, test_case, k):
    # >>> implement
    scored = [(euc_dist(row[:-1], test_case), row) for row in train_data]
    scored.sort(key=lambda pair: pair[0])
    return [row for _, row in scored[:k]]
    # <<< implement

def get_label(train_data, test_case, k):
    neighbors = k_neighbors(train_data, test_case, k)
    labels = [row[-1] for row in neighbors]
    max_label = max(set(labels), key=labels.count)
    return max_label

def knn_solution(train_data, test_data, k):
    final_labels = list()
    for row in test_data:
        label = get_label(train_data, row, k)
        final_labels.append(label)
    return final_labels


# ==== kmeans ====
# k-Means: assign each point to its nearest centroid, recompute centroids as the
# coordinate-wise mean, stop when nothing moves. An empty cluster keeps its old centroid.
def assign_clusters(points, centroids):
    # >>> implement
    labels = []
    for p in points:
        dists = [euc_dist(p, c) for c in centroids]
        labels.append(dists.index(min(dists)))
    return labels
    # <<< implement

def update_centroids(points, labels, old_centroids):
    # >>> implement
    new_centroids = []
    for j, old in enumerate(old_centroids):
        members = [p for p, lab in zip(points, labels) if lab == j]
        if not members:
            new_centroids.append(list(old))
            continue
        dim = len(members[0])
        new_centroids.append([sum(m[d] for m in members) / len(members) for d in range(dim)])
    return new_centroids
    # <<< implement

def kmeans(points, init_centroids, max_iter=100):
    centroids = [list(c) for c in init_centroids]
    labels = assign_clusters(points, centroids)
    for _ in range(max_iter):
        new_centroids = update_centroids(points, labels, centroids)
        new_labels = assign_clusters(points, new_centroids)
        centroids = new_centroids
        if new_labels == labels:
            break
        labels = new_labels
    return labels, centroids


# ==== normalize ====
# Matrix normalization, three flavours. Column-wise for min-max and z-score; row-wise for L2.
# Use the POPULATION standard deviation (divide by n) unless the task says otherwise.
def minmax_normalize(matrix):
    # >>> implement
    cols = list(zip(*matrix))
    lows = [min(c) for c in cols]
    highs = [max(c) for c in cols]
    out = []
    for row in matrix:
        out.append([(v - lo) / (hi - lo) if hi != lo else 0.0
                    for v, lo, hi in zip(row, lows, highs)])
    return out
    # <<< implement

def zscore_normalize(matrix):
    # >>> implement
    cols = list(zip(*matrix))
    means = [sum(c) / len(c) for c in cols]
    stds = [(sum((v - m) ** 2 for v in c) / len(c)) ** 0.5 for c, m in zip(cols, means)]
    return [[(v - m) / s if s else 0.0 for v, m, s in zip(row, means, stds)] for row in matrix]
    # <<< implement

def l2_normalize_rows(matrix):
    # >>> implement
    out = []
    for row in matrix:
        norm = sum(v * v for v in row) ** 0.5
        out.append([v / norm if norm else 0.0 for v in row])
    return out
    # <<< implement


# ==== forward ====
# Forward propagation. weights[j][i] is the weight from input i to neuron j.
# layers is a list of (weights, biases, activation) tuples applied in order.
def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))

def relu(x):
    return x if x > 0 else 0.0

def linear(x):
    return x

def dense(inputs, weights, biases, activation):
    # >>> implement
    outputs = []
    for j, w_row in enumerate(weights):
        z = sum(w * x for w, x in zip(w_row, inputs)) + biases[j]
        outputs.append(activation(z))
    return outputs
    # <<< implement

def forward(inputs, layers):
    # >>> implement
    activations = list(inputs)
    for weights, biases, activation in layers:
        activations = dense(activations, weights, biases, activation)
    return activations
    # <<< implement


# ==== tree ====
# Decision-tree pieces: impurity, a threshold split, and the best (feature, threshold)
# by weighted Gini. rows carry features first and the class label LAST.
def gini(labels):
    # >>> implement
    n = len(labels)
    if n == 0:
        return 0.0
    return 1.0 - sum((labels.count(c) / n) ** 2 for c in set(labels))
    # <<< implement

def entropy(labels):
    # >>> implement
    n = len(labels)
    if n == 0:
        return 0.0
    total = 0.0
    for c in set(labels):
        p = labels.count(c) / n
        total -= p * math.log2(p)
    return total
    # <<< implement

def split_rows(rows, feature, threshold):
    left = [r for r in rows if r[feature] <= threshold]
    right = [r for r in rows if r[feature] > threshold]
    return left, right

def best_split(rows):
    # >>> implement
    best_feature, best_threshold, best_score = None, None, float("inf")
    n = len(rows)
    for feature in range(len(rows[0]) - 1):
        for threshold in sorted(set(r[feature] for r in rows)):
            left, right = split_rows(rows, feature, threshold)
            if not left or not right:
                continue
            score = (len(left) / n) * gini([r[-1] for r in left]) \
                  + (len(right) / n) * gini([r[-1] for r in right])
            if score < best_score:
                best_feature, best_threshold, best_score = feature, threshold, score
    return best_feature, best_threshold, best_score
    # <<< implement


# ==== bagging ====
# Bagging: n bootstrap samples (with replacement, same size as the data), one base
# model each, majority vote at prediction. `fit(rows) -> model`, `predict(model, row) -> label`.
def bootstrap_sample(rows, rng):
    # >>> implement
    return [rng.choice(rows) for _ in range(len(rows))]
    # <<< implement

def majority_vote(predictions):
    return max(set(predictions), key=predictions.count)

def bagging_predict(train_data, test_data, n_models, fit, predict, seed=0):
    # >>> implement
    rng = random.Random(seed)
    models = [fit(bootstrap_sample(train_data, rng)) for _ in range(n_models)]
    results = []
    for row in test_data:
        votes = [predict(model, row) for model in models]
        results.append(majority_vote(votes))
    return results
    # <<< implement


# ==== gmm ====
# 1-D Gaussian mixture by EM. E-step: responsibilities. M-step: weighted mean/variance/weight.
def gaussian_pdf(x, mean, var):
    return math.exp(-((x - mean) ** 2) / (2.0 * var)) / math.sqrt(2.0 * math.pi * var)

def e_step(xs, weights, means, variances):
    # >>> implement
    resp = []
    for x in xs:
        numer = [w * gaussian_pdf(x, m, v) for w, m, v in zip(weights, means, variances)]
        total = sum(numer)
        resp.append([n / total for n in numer])
    return resp
    # <<< implement

def m_step(xs, resp):
    # >>> implement
    k = len(resp[0])
    n = len(xs)
    weights, means, variances = [], [], []
    for j in range(k):
        r_j = [r[j] for r in resp]
        n_j = sum(r_j)
        mean = sum(r * x for r, x in zip(r_j, xs)) / n_j
        var = sum(r * (x - mean) ** 2 for r, x in zip(r_j, xs)) / n_j
        weights.append(n_j / n)
        means.append(mean)
        variances.append(max(var, 1e-6))
    return weights, means, variances
    # <<< implement

def gmm_1d(xs, init_means, iters=50):
    k = len(init_means)
    weights = [1.0 / k] * k
    means = list(init_means)
    variances = [1.0] * k
    for _ in range(iters):
        resp = e_step(xs, weights, means, variances)
        weights, means, variances = m_step(xs, resp)
    return weights, means, variances


# ==== extras ====
# Cheap extras that fit the same "implement from a description" mould.
def manhattan_dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0

def softmax(zs):
    m = max(zs)
    exps = [math.exp(z - m) for z in zs]
    s = sum(exps)
    return [e / s for e in exps]

def linear_regression_gd(xs, ys, lr=0.01, epochs=1000):
    # y = w * x + b, batch gradient descent on MSE
    w = b = 0.0
    n = len(xs)
    for _ in range(epochs):
        preds = [w * x + b for x in xs]
        dw = (2.0 / n) * sum((p - y) * x for p, y, x in zip(preds, ys, xs))
        db = (2.0 / n) * sum(p - y for p, y in zip(preds, ys))
        w -= lr * dw
        b -= lr * db
    return w, b

def logistic_step(weights, bias, xs, ys, lr):
    # one batch gradient-descent step on log loss; xs is a list of feature rows
    n = len(xs)
    grads = [0.0] * len(weights)
    grad_b = 0.0
    for row, y in zip(xs, ys):
        p = sigmoid(sum(w * x for w, x in zip(weights, row)) + bias)
        err = p - y
        for i, x in enumerate(row):
            grads[i] += err * x / n
        grad_b += err / n
    return [w - lr * g for w, g in zip(weights, grads)], bias - lr * grad_b

def precision_recall_f1(y_true, y_pred, positive=1):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


# ==== tests ====
BRIEF_TRAIN = [[-2.6, 1.9, 2.0, 1.0, 1.0],
               [-2.8, 1.7, -1.2, 1.5, 2.0],
               [2.0, -0.9, 0.3, 2.3, 0.0],
               [-1.5, -0.1, -1.6, -1.1, 0.0],
               [-1.0, -0.6, -1.2, -0.7, 0.0],
               [-0.3, 1.2, 2.6, 0.2, 1.0],
               [-1.8, -1.3, -0.1, -1.2, 0.0],
               [0.2, 1.2, -0.6, -1.3, 1.0],
               [-5.2, 0.3, 0.2, 2.2, 2.0],
               [-0.8, -0.1, 1.5, -0.1, 0.0],
               [-2.3, 0.3, 0.8, 0.7, 2.0],
               [0.2, 3.0, 3.6, -0.9, 1.0],
               [1.7, -0.8, -0.0, 2.0, 0.0],
               [2.8, 0.8, 1.8, -0.7, 2.0]]
BRIEF_TEST = [[-0.1, 1.4, 0.4, -1.0],
              [-1.3, 0.2, -1.3, -0.8],
              [-1.1, 1.5, -2.3, -2.5],
              [0.2, 2.0, -0.1, -0.8],
              [-0.3, -1.6, -3.4, -1.4]]


def _close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_module_2():
    assert triple_duplicate_words("Dooddle moodle Pepper unsuccessfully") == 3
    assert triple_duplicate_words("aaa bbb c") == 2
    assert triple_duplicate_words("") == 0
    assert digit_balance(31724) == -5
    assert digit_balance(-2468) == 20
    assert split_and_prepend([3, -1, 4, -5, 0]) == [-5, -1, 3, 4, 0]
    assert split_and_prepend([]) == []
    assert reverse_long_words("the quick brown fox", 4) == "the kciuq nworb fox"
    assert anagram_pairs("Listen silent enlist tinsel banana") == 6

def test_knn():
    assert knn_solution(BRIEF_TRAIN, BRIEF_TEST, 3) == [1.0, 0.0, 0.0, 1.0, 0.0]
    assert _close(euc_dist([0, 0], [3, 4]), 5.0)

def test_kmeans():
    pts = [[0, 0], [0.5, 0.2], [-0.3, 0.1], [10, 10], [9.7, 10.2], [10.3, 9.9]]
    labels, cents = kmeans(pts, [[3, 3], [6, 6]])
    assert labels == [0, 0, 0, 1, 1, 1]
    assert _close(cents[1][0], 10.0) and _close(cents[1][1], 10.0333333, 1e-6)

def test_normalize():
    assert minmax_normalize([[1, 10], [2, 20], [3, 30]]) == [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]
    z = zscore_normalize([[1], [2], [3]])
    assert _close(z[0][0], -1.2247448714) and _close(z[1][0], 0.0)
    assert l2_normalize_rows([[3, 4]]) == [[0.6, 0.8]]

def test_forward():
    layers = [([[0.5, -0.2], [0.1, 0.4]], [0.0, 0.0], linear),
              ([[0.3, 0.7]], [0.0], sigmoid)]
    out = forward([1.0, 2.0], layers)
    hidden = dense([1.0, 2.0], [[0.5, -0.2], [0.1, 0.4]], [0.0, 0.0], linear)
    assert _close(hidden[0], 0.1) and _close(hidden[1], 0.9)
    assert round(out[0], 3) == 0.659
    assert forward([1.0], [([[-2.0]], [0.5], relu)]) == [0.0]

def test_tree():
    assert _close(gini([0, 0, 1, 1]), 0.5)
    assert _close(gini([1, 1, 1]), 0.0)
    assert _close(entropy([0, 1]), 1.0)
    assert best_split([[1, 0], [2, 0], [3, 1], [4, 1]]) == (0, 2, 0.0)
    f, t, s = best_split([[1, 5, 0], [2, 6, 0], [3, 1, 1], [4, 2, 1], [5, 7, 0]])
    assert f == 1 and t == 2 and _close(s, 0.0)

def test_bagging():
    train = [[-3.0, 0.0], [-2.0, 0.0], [-1.0, 0.0], [1.0, 1.0], [2.0, 1.0], [3.0, 1.0]]
    preds = bagging_predict(train, [[-5.0], [5.0]], 7,
                            fit=lambda rows: rows,
                            predict=lambda model, row: get_label(model, row, 1))
    assert preds == [0.0, 1.0]
    assert len(bootstrap_sample(train, random.Random(1))) == len(train)

def test_gmm():
    xs = [0.0, 0.2, -0.1, 0.1, 10.0, 10.2, 9.9, 10.1]
    w, m, v = gmm_1d(xs, [3.0, 6.0])
    assert sorted(round(x, 2) for x in m) == [0.05, 10.05]
    assert _close(sum(w), 1.0)

def test_extras():
    assert manhattan_dist([1, 2], [4, 6]) == 7
    assert _close(cosine_similarity([1, 0], [1, 0]), 1.0)
    assert _close(sum(softmax([1.0, 2.0, 3.0])), 1.0)
    w_, b_ = linear_regression_gd([1, 2, 3, 4], [3, 5, 7, 9], lr=0.05, epochs=5000)
    assert round(w_, 2) == 2.0 and round(b_, 2) == 1.0
    p, r, f1 = precision_recall_f1([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    assert _close(p, 2 / 3) and _close(r, 2 / 3) and _close(f1, 2 / 3)
    ws, bs = logistic_step([0.0], 0.0, [[1.0], [-1.0]], [1, 0], 0.1)
    assert ws[0] > 0.0

TESTS = [test_module_2, test_knn, test_kmeans, test_normalize, test_forward, test_tree, test_bagging, test_gmm, test_extras]


def run_tests():
    failed = 0
    for test in TESTS:
        try:
            test()
            print("PASS", test.__name__[5:])
        except AssertionError as exc:
            failed += 1
            print("FAIL", test.__name__[5:], "-", exc or "assertion failed")
        except Exception as exc:  # a blank skeleton returns None and trips here
            failed += 1
            print("FAIL", test.__name__[5:], "-", type(exc).__name__ + ": " + str(exc))
    print("ALL PASS" if not failed else f"{failed} section(s) failing")
    return failed


if __name__ == "__main__":
    raise SystemExit(1 if run_tests() else 0)
