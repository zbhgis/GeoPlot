"""
-------------------------------------------------------------------------------
@Author         :  zbhgis
@Github         :  https://github.com/zbhgis
@Description    :  paleogeography map (Hammer Projection)
@Data           :  https://zenodo.org/records/5460860
-------------------------------------------------------------------------------
"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from pathlib import Path
import os
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import Normalize


# 基本配置
plt.rcParams["font.family"] = "Arial"
nc_name = "paleo_6min_100Ma"
nc_file = Path(f"../data_res/{nc_name}.nc")

# 图幅和投影
proj = ccrs.Hammer()
fig = plt.figure(figsize=(10, 6), dpi=100)
ax = fig.add_subplot(1, 1, 1, projection=proj)

# 设置范围
ax.set_global()

# 设置色带
# 定义海洋色系
ocean_colors = [
    "#102A51",
    "#173E67",
    "#2B94C9",
    "#7EC7E1",
]

# 定义陆地色系
land_colors = [
    "#325C39",
    "#55975F",
    "#98B487",
    "#d4a76a",
    "#b08968",
    "#9D6B40",
    "#865D39",
    "#6D4C2E",
    "#473224",
    "#301C10",
]


# 创建以0值为分界点的渐变色带
def create_zero_based_colormap(vmin, vmax, ocean_colors, land_colors, N=256):

    # 计算0值在色带中的位置比例
    # 全是非负值，只使用陆地色带;全是非正值，只使用海洋色带
    if vmin >= 0:
        cmap = LinearSegmentedColormap.from_list("land_only", land_colors, N=N)
        return cmap, Normalize(vmin=vmin, vmax=vmax)
    if vmax <= 0:
        cmap = LinearSegmentedColormap.from_list("ocean_only", ocean_colors, N=N)
        return cmap, Normalize(vmin=vmin, vmax=vmax)

    # 有正有负的情况
    # 计算负值和正值的范围比例
    negative_range = abs(vmin)  # 负值范围
    positive_range = vmax  # 正值范围
    total_range = negative_range + positive_range

    # 创建分段色带
    zero_position = negative_range / total_range
    ocean_length = int(N * zero_position)
    land_length = N - ocean_length

    # 确保至少有一个颜色
    ocean_length = max(ocean_length, 1)
    land_length = max(land_length, 1)

    # 创建两个子色带
    ocean_cmap = LinearSegmentedColormap.from_list(
        "ocean_segment", ocean_colors, N=ocean_length
    )
    land_cmap = LinearSegmentedColormap.from_list(
        "land_segment", land_colors, N=land_length
    )

    # 拼接
    ocean_colors_array = ocean_cmap(np.linspace(0, 1, ocean_length))
    land_colors_array = land_cmap(np.linspace(0, 1, land_length))
    combined_colors = np.vstack((ocean_colors_array, land_colors_array))
    cmap = LinearSegmentedColormap.from_list("zero_based_terrain", combined_colors, N=N)

    return cmap, Normalize(vmin=vmin, vmax=vmax)


vmin = -6000
vmax = 4000
terrain_map, norm = create_zero_based_colormap(vmin, vmax, ocean_colors, land_colors)

# 提前设置好导出文件路径
script_name = os.path.splitext(os.path.basename(__file__))[0]
folder_path = os.path.join("../fig_res", script_name)
os.makedirs(folder_path, exist_ok=True)
output_filename = f"{script_name}_{nc_name}.png"
output_path = os.path.join(folder_path, output_filename)

# 读取数据并绘制
ds = xr.open_dataset(nc_file)
data = ds["z"].values
lats = ds["latitude"].values
lons = ds["longitude"].values
ds.close()

im = ax.imshow(
    data,
    extent=[lons.min(), lons.max(), lats.min(), lats.max()],
    transform=ccrs.PlateCarree(),
    origin="upper",
    cmap=terrain_map,
    norm=norm,
    interpolation="bilinear",
)

# 添加DEM色带
cbar = fig.colorbar(
    im, ax=ax, orientation="horizontal", pad=0.04, aspect=40, shrink=0.6, extend="both"
)
cbar.set_label("Elevation (m)", fontsize=14)

# 添加现在的矢量边界
ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="black")
ax.set_title(nc_name, fontsize=16, pad=15)

plt.savefig(output_path, dpi=100, bbox_inches="tight")
plt.close(fig)
print("ok")
