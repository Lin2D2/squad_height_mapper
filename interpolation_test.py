import math
import os
import shutil

from time import perf_counter

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from PIL import Image

start = perf_counter()

folder_name = "Yehorivka_AAS_v4"
mapper_data_files = list(sorted(filter(lambda o: o.lower().find("mapperoutput") != -1,
                                               os.listdir(folder_name)),
                                key=lambda name: int(name.split("_")[-2])))

with open('Yehorivka_AAS_v4_mapperOutput.csv', 'wb') as wfd:
    wfd.write(b"id,location_x,location_y,location_z,impact_normal_x,impact_normal_y,impact_normal_z,"
              b"hit_actor,hit_component,material\n")
    for f in mapper_data_files:
        with open(os.path.join(folder_name, f), 'rb') as fd:
            shutil.copyfileobj(fd, wfd)

print(f"combining files took: {perf_counter()-start}")
start = perf_counter()

point_data = pd.read_csv("Yehorivka_AAS_v4_mapperOutput.csv")

print(f"read file took: {perf_counter()-start}")

# li = []
# for filename in mapper_data_files:
#     df = pd.read_csv(os.path.join(folder_name, filename), index_col=None, header=0)
#     li.append(df)
#
# point_data = pd.concat(li, axis=0, ignore_index=True)

point_data_landscape = point_data["hit_actor"].str.contains("landscape")

resolution = int(math.sqrt(point_data["id"][point_data_landscape].max())) + 1
x_min = point_data["location_x"][point_data_landscape].min()
x_max = point_data["location_x"][point_data_landscape].max()
y_min = point_data["location_y"][point_data_landscape].min()
y_max = point_data["location_y"][point_data_landscape].max()
z_min = point_data["location_z"][point_data_landscape].min()
z_max = point_data["location_z"][point_data_landscape].max()

x_extend = abs(x_max) + abs(x_min)
y_extend = abs(y_max) + abs(y_min)

step_size = x_extend / resolution


def get_index_from_coordinates(x_a, x_i, y_a, y_i):
    if x_a > 0:
        x_start = (abs(x_a) + abs(x_min)) // step_size
    else:
        x_start = (abs(x_min) - abs(x_a)) // step_size
    if x_i > 0:
        x_end = (abs(x_i) + abs(x_min)) // step_size
    else:
        x_end = (abs(x_min) - abs(x_i)) // step_size
    if y_a > 0:
        y_start = (abs(y_a) + abs(y_min)) // step_size
    else:
        y_start = (abs(y_min) - abs(y_a)) // step_size
    if y_i > 0:
        y_end = (abs(y_i) + abs(y_min)) // step_size
    else:
        y_end = (abs(y_min) - abs(y_i)) // step_size
    if x_start == x_end:
        x = x_start
    else:
        x = (x_end - x_start) // 2 + x_start
    if y_start == y_end:
        y = y_start
    else:
        y = (y_end - y_start) // 2 + y_start
    return int(y * resolution + x)


start = perf_counter()

location_x = point_data.location_x[point_data_landscape]
location_y = point_data.location_y[point_data_landscape]
location_z = point_data.location_z[point_data_landscape]

x_list = np.linspace(location_x.min(), location_x.max(), resolution)
y_list = np.linspace(location_y.min(), location_y.max(), resolution)
z_list = np.linspace(location_z.min(), location_z.max(), resolution)

location_z_id = point_data[["id", "location_z"]][point_data_landscape]

matrix = np.zeros((resolution * resolution))
matrix.put(location_z_id.id, location_z_id.location_z)
Z = np.flip(matrix.reshape((resolution, resolution)), axis=0)

X, Y = np.meshgrid(x_list, y_list)


fig = plt.figure(figsize=(resolution / 1000, resolution / 1000), dpi=1000)
fig.patch.set_facecolor('black')
left, bottom, width, height = 0.00001, 0.00001, 0.99999, 0.99999
ax = fig.add_axes([left, bottom, width, height])

cp = ax.contour(X, Y, Z, colors="white", linestyles="solid",
                linewidths=(resolution / 1000 / 1000 / 10), levels=10, antialiased=False)

height_lines = np.zeros((resolution * resolution, 3), dtype=np.uint8)

print(f"time prepare took: {perf_counter() - start}")
start = perf_counter()

min_segments = 200
label_segment_spacing = 1500
label_side_spacing = 100
labels = []
for level_num, level in zip(cp.levels, cp.allsegs):
    for contour in level:
        if len(contour) < min_segments:
            continue
        for i, (x, y) in enumerate(contour):
            cord = get_index_from_coordinates(x, x, y, y)
            if cord > height_lines.size / 3 - 1:
                continue
            height_lines[cord] = (255, 255, 255)
            if i == 0:
                labels.append((x, y))
                continue
            if i % label_segment_spacing == 0 and len(contour) - label_segment_spacing > 0:
                if x < 0:
                    if x - label_side_spacing < x_min:
                        continue
                else:
                    if x + label_side_spacing > x_max:
                        continue
                if y < 0:
                    if y - label_side_spacing < y_min:
                        continue
                else:
                    if y + label_side_spacing > y_max:
                        continue
                labels.append((x, y))

print(f"time segments took: {perf_counter() - start}")
print(f"labels: {len(labels)}")

height_lines = np.flip(height_lines.reshape((resolution, resolution, 3)), axis=0)

start = perf_counter()
clabels = ax.clabel(cp, colors="red", inline=True, rightside_up=True,
                    fontsize=1,  manual=labels)
clabels_list = list(clabels)
print(f"time labels took: {perf_counter() - start}")
start = perf_counter()
plt.axis('off')
plt.draw()
fig.canvas.draw()
print(f"time draw took: {perf_counter() - start}")
start = perf_counter()

final_data_with_labels = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape((resolution, resolution, 3))

data_labels = np.full((resolution, resolution, 3), (0, 0, 0), dtype=np.uint8)
without_labels = np.copy(final_data_with_labels)

red, green, blue = final_data_with_labels.T

area = ((red > 10) | (blue > 10) | (green > 10)) & ((red != 255) & (blue != 255) & (green != 255))
data_labels[area.T] = (255, 255, 255)
without_labels[area.T] = (0, 0, 0)

height_lines_with_gaps = np.bitwise_and(height_lines, without_labels)
combined_data = np.bitwise_or(data_labels, height_lines_with_gaps)
print(f"time diff took: {perf_counter() - start}")

image = Image.fromarray(combined_data)
image.save("data_diff.png")
# breakpoint()
