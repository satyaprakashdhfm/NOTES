# Jupyter Notebook Markdown and Equation Syntax Guide

## Basic Markdown Syntax

### Headers
```
# Header 1
## Header 2
### Header 3
```

### Text Formatting
```
*Italic text* or _italic text_
**Bold text** or __bold text__
***Bold and italic*** or ___bold and italic___
~~Strikethrough text~~
```

### Lists
```
* Unordered list item
* Another item
  * Nested item
    * Further nested

1. Ordered list item
2. Second item
   1. Nested numbered item
```

## Mathematical Equations

### Inline Equations
Use single dollar signs for inline equations:
```
This is an inline equation: $E = mc^2$
```

### Display Equations
Use double dollar signs for centered display equations:
```
$$
\begin{equation}
F = ma
\end{equation}
$$
```

### Common Mathematical Notation
```
$$
\sum_{i=1}^{n} x_i        # Summation
\prod_{i=1}^{n} x_i       # Product
\frac{numerator}{denominator}  # Fractions
\sqrt{x}                   # Square root
\sqrt[n]{x}               # nth root
\vec{F}                   # Vector
\bar{x}                   # Mean
\partial x                # Partial derivative
\int_{a}^{b} f(x)dx      # Integral
\lim_{x \to \infty}      # Limit
```

### Matrix Notation
```
$$
\begin{matrix}
a & b \\
c & d
\end{matrix}
$$

$$
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
$$
```

## Code Blocks

### Code Cell Formatting
```python
# Python code block
def example_function():
    return "Hello World"
```

```R
# R code block
example_function <- function() {
    return("Hello World")
}
```

### Inline Code
Use backticks for inline code: `variable_name`

## Advanced Features

### Tables
```
| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

### Block Quotes
```
> This is a block quote
> It can span multiple lines
```

### Horizontal Rule
```
---
```

### Links and Images
```
[Link text](URL)
![Image alt text](image_URL)
```

### HTML in Markdown
Jupyter Notebook also supports HTML:
```html
<div style="color: blue;">
    Colored text using HTML
</div>
```

## Tips for Mathematical Documents

### Equation Numbering
```
$$
\begin{equation}
E = mc^2 \tag{1}
\end{equation}
$$
```

### Aligned Equations
```
$$
\begin{align}
y &= mx + b \\
&= 2x + 3
\end{align}
$$
```

### Cases
```
$$
f(x) = \begin{cases}
x^2 & \text{if } x > 0 \\
0 & \text{if } x = 0 \\
-x^2 & \text{if } x < 0
\end{cases}
$$
```