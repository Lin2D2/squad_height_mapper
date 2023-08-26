import math

from time import perf_counter

import pandas as pd
import numpy as np

from scipy.interpolate import RegularGridInterpolator, Rbf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from PIL import Image, ImageFont, ImageDraw


point_data = pd.read_csv('Yehorivka_AAS_v8_mapperOutput.csv')
default_font = ImageFont.truetype("Cygre-Regular.ttf", 12)

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
    # TODO add rotation
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

    # just sets to middle of object
    # TODO in future return start and end points
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

# interp = RegularGridInterpolator((x_list, y_list), Z)

fig = plt.figure(figsize=(resolution / 1000, resolution / 1000), dpi=1000)
fig.patch.set_facecolor('black')
left, bottom, width, height = 0.00001, 0.00001, 0.99999, 0.99999
ax = fig.add_axes([left, bottom, width, height])
# ax.set_facecolor((0, 0, 0))

cp = ax.contour(X, Y, Z, colors="white", linestyles="solid",
                linewidths=(resolution / 1000 / 1000 / 10), levels=10, antialiased=False)

height_lines = np.zeros((resolution * resolution, 3), dtype=np.uint8)

print(f"time prepare took: {perf_counter() - start}")
start = perf_counter()

min_segments = 200
label_segment_spacing = 1500
label_side_spacing = 100
# segments = []
labels = []
for level_num, level in zip(cp.levels, cp.allsegs):
    for contour in level:
        if len(contour) < min_segments:
            continue
        for i, (x, y) in enumerate(contour):
            cord = get_index_from_coordinates(x, x, y, y)
            if cord > height_lines.size / 3 - 1:
                continue
            # height_lines.put(cord, (255, 255, 255))
            height_lines[cord] = (255, 255, 255)
            if i == 0:
                # labels.append(((x, y), level_num))
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
                # labels.append(((x, y), level_num))
                labels.append((x, y))

print(f"time segments took: {perf_counter() - start}")
print(f"labels: {len(labels)}")

# TODO fix overlapping of lines and text
height_lines = np.flip(height_lines.reshape((resolution, resolution, 3)), axis=0)
image = Image.fromarray(height_lines)
# draw = ImageDraw.Draw(image)
# for pos, level in labels:
#     location = get_index_from_coordinates(pos[0], pos[0], pos[1], pos[1])
#     draw.text((location % resolution, location // resolution), f"{level}",
#               fill="white", font=default_font)
image.save("height_lines.png")

start = perf_counter()
clabels = ax.clabel(cp, colors="red", inline=True, rightside_up=True,
                    fontsize=1,  manual=labels)
clabels_list = list(clabels)
print(f"time labels took: {perf_counter() - start}")
# ax.clabel(cp, inline=True, fontsize=2, rightside_up=True, manual=labels)
start = perf_counter()
plt.axis('off')
plt.draw()
print(f"time draw took: {perf_counter() - start}")
start = perf_counter()

# TODO do cleaner
final_data_with_labels = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
final_data_with_labels = final_data_with_labels.reshape((resolution, resolution, 3))

final_data = np.full((resolution, resolution, 3), (0, 0, 0), dtype=np.uint8)

red, green, blue = final_data_with_labels.T

area = ((red > 10) | (blue > 10) | (green > 10)) & ((red != 255) & (blue != 255) & (green != 255))
final_data[area.T] = (255, 255, 255)

red, green, blue = height_lines.T

area = (red > 10) | (blue > 10) | (green > 10)
final_data[area.T] = (255, 255, 255)
# TODO do smarter mapping to white with shading intact
# TODO fix overlapping of text and lines

print(f"time diff took: {perf_counter() - start}")

image = Image.fromarray(final_data)
image.save("data_diff.png")
# breakpoint()
