import matplotlib.pyplot as plt
# Data for Histogram
# Data for Pie Chart
X=[34,89,12,78]
# ’autopct’ displays the percentage upto 1 decimal place
# ’radius’ sets the radius of the the pie plot
plt.figure(figsize=(6,6))
plt.pie(X, autopct = '%.1f%%',radius = 1.2,labels =['sat','sun','Thur','Fri'])
plt.show()