import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

gold_df = pd.read_csv('/content/gold.csv')
# print(gold_df.to_markdown())
x = gold_df['city_population']
y = gold_df['visitor_count']

# model
model = np.polyfit(x, y, deg=1)
correlation_coefficient = np.corrcoef(x, y)[0, 1]
if abs(correlation_coefficient) < 0.3:
  print(f'poorly correlated: {correlation_coefficient}')
else:
  print(f'correlated: {correlation_coefficient}')

slope, intercept = model
regression_line = slope * x + intercept

# Plot
plt.scatter(x, y, label='Data')
plt.plot(x, regression_line, color='red', label='Regression Line')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Regression Plot')
plt.legend()


plt.show()
