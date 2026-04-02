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
import xarray as xr
from pathlib import Path
import os
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import Normalize
from matplotlib.colors import LightSource
from scipy.ndimage import gaussian_filter


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

# 设置色带，这个配色专门为这个数据调整的，仅供参考
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

# 读取数据
ds = xr.open_dataset(nc_file)
data = ds["z"].values
lats = ds["latitude"].values
lons = ds["longitude"].values
ds.close()

# 参数配置：(hillshade_alpha, base_alpha, suffix)
param_groups = [
    (0.20, 0.9, "soft"),
    (0.35, 0.8, "extreme"),
    (0, 0.8, "light"),
    (0, 1, "normal"),
]


sigma = 1.5  # 模糊半径，增加结果的光滑度
data = gaussian_filter(data, sigma=sigma)
ls = LightSource(azdeg=315, altdeg=45)

# 生成不同参数的图
for hs_alpha, base_alpha, suffix in param_groups:
    fig = plt.figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Hammer())
    ax.set_global()

    # 绘制基础地形色带
    im = ax.imshow(
        data,
        extent=[lons.min(), lons.max(), lats.min(), lats.max()],
        transform=ccrs.PlateCarree(),
        origin="upper",
        cmap=terrain_map,
        norm=norm,
        interpolation="spline36",
        alpha=base_alpha,
    )

    # 生成山体阴影
    hillshade = ls.hillshade(data, dx=1, dy=1)

    # 叠加山体阴影层
    ax.imshow(
        hillshade,
        extent=[lons.min(), lons.max(), lats.min(), lats.max()],
        transform=ccrs.PlateCarree(),
        origin="upper",
        cmap="gray",
        alpha=hs_alpha,
        interpolation="bilinear",
    )

    # 添加色带
    cbar = fig.colorbar(
        im,
        ax=ax,
        orientation="horizontal",
        pad=0.04,
        aspect=40,
        shrink=0.6,
        extend="neither",
    )
    cbar.set_label("Elevation (m)", fontsize=14)

    # 手动在左侧添加纬度标记，用默认的绘制容易出错
    gl = ax.gridlines(
        draw_labels=False,
        linewidth=0,
        alpha=0,
    )
    lat_nums = [-60, -30, 0, 30, 60]
    lat_labels = [
        "60°S     ",
        "30°S   ",
        "0° ",
        "30°N   ",
        "60°N     ",
    ]
    for lat_num, lat_label in zip(lat_nums, lat_labels):
        ax.text(
            -180,  # 标签的经度坐标
            lat_num,  # 标签纬度坐标
            lat_label,  # 增大与边界的距离
            transform=ccrs.PlateCarree(),
            fontsize=9,
            color="black",
            ha="right",
            va="center",
        )

    # 添加标题
    ax.set_title(f"{nc_name} - {suffix}", fontsize=14, pad=15)

    # 保存
    output_filename = f"{script_name}_{nc_name}_{suffix}.png"
    output_path = os.path.join(folder_path, output_filename)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(output_filename)

print("ok")
