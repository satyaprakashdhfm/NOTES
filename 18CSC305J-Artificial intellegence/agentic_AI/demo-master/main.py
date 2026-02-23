from numpy import array, dot
from numpy.linalg import norm

def cosine_similarity(vec_a, vec_b):
    return dot(vec_a, vec_b) / (norm(vec_a) * norm(vec_b))

new1 = array([1, 2, 3])
new2 = array([4, 5, 6])
result1 = cosine_similarity(new1, new2)
print("Cosine Similarity:", result1)