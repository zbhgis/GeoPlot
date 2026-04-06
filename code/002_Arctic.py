"""
-------------------------------------------------------------------------------
@Author         :  zbhgis
@Github         :  https://github.com/zbhgis
@Description    :  Arctic-square
@Data           :  https://download.gebco.net/
-------------------------------------------------------------------------------
"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.colors as mcolors
import importlib.util
import numpy as np
import os
import rasterio

# 基本配置
plt.rcParams["font.family"] = "Arial"
boundary_shp = "../data_res/country.shp"
dem_tif = "../data_res/cop_dem.tif"
dem_nodata = 0

# 色带设置，不通过import导入，在其他环境下可能报错
colors_path = "../colors/002_colors.py"
spec = importlib.util.spec_from_file_location("custom_colors", colors_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
color_dict = module.color_maps
color_names = list(color_dict.keys())

for color_name in color_names:
    # 两种投影在绘制极地小区域时可互相替换
    # proj = ccrs.Orthographic(0, 90, 0)
    proj = ccrs.NorthPolarStereo()
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(1, 1, 1, projection=proj)

    # 设置范围
    ax.set_extent([-180, 180, 30, 90], crs=ccrs.PlateCarree())
    output_color = color_dict[color_name]
    cmap = mcolors.ListedColormap(output_color)
    levels = np.linspace(0, 1000, cmap.N + 1)
    norm = mcolors.BoundaryNorm(levels, ncolors=cmap.N, clip=True)

    # 提前设置好导出文件路径
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    folder_path = os.path.join("../fig_res", script_name)
    os.makedirs(folder_path, exist_ok=True)
    output_filename = f"{script_name}_{color_name}.png"
    output_path = os.path.join(folder_path, output_filename)

    # 读取dem并绘制
    with rasterio.open(dem_tif) as src:
        dem_data = src.read(1, masked=True)

        dem_data = np.ma.masked_where(dem_data == dem_nodata, dem_data)

        left, bottom, right, top = src.bounds
        extent = [left, right, bottom, top]

        im = ax.imshow(
            dem_data,
            extent=extent,
            transform=ccrs.PlateCarree(),
            origin="upper",
            cmap=cmap,
            norm=norm,
            alpha=0.8,
            interpolation="nearest",
            zorder=0,
        )

    # 添加矢量边界数据
    reader = shpreader.Reader(boundary_shp)
    boundary_feature = cfeature.ShapelyFeature(
        reader.geometries(),
        ccrs.PlateCarree(),
        facecolor="none",
        edgecolor="#838383",
        linewidth=0.5,
        alpha=0.8,
        linestyle="-",
    )
    ax.add_feature(boundary_feature, zorder=10)

    # 添加DEM色带
    cbar = fig.colorbar(
        im,
        ax=ax,
        orientation="horizontal",
        pad=0.06,  # 色带与主图距离
        aspect=25,  # 色带粗细
        shrink=0.7,  # 色带长度
    )

    # 将边框线调整为无色
    for spine in cbar.ax.spines.values():
        spine.set_visible(False)

    # 设置色带刻度
    cbar.set_ticks(levels)
    cbar.set_ticklabels([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    cbar.ax.tick_params(
        labelsize=14,
        labelcolor="black",
        length=0,
    )

    # 设置色带文本与箭头
    cbar.ax.text(
        x=0.5,
        y=1.15,
        s="Elevation (km)",
        ha="center",
        va="bottom",
        fontsize=16,
        transform=cbar.ax.transAxes,
    )
    cbar.ax.plot(
        [0.5, 0.5],
        [-1.4, -4],
        color="black",
        linewidth=1,
        linestyle="-",
        transform=cbar.ax.transAxes,
        clip_on=False,
    )
    cbar.ax.arrow(
        x=0.55,
        y=-1.3,
        dx=0.15,
        dy=0,
        width=0.008,
        head_width=0.4,
        head_length=0.02,
        fc="black",
        ec="black",
        linewidth=1.5,
        length_includes_head=True,
        transform=cbar.ax.transAxes,
        clip_on=False,
    )
    cbar.ax.arrow(
        x=0.45,
        y=-1.3,
        dx=-0.15,
        dy=0,
        width=0.008,
        head_width=0.4,
        head_length=0.02,
        fc="black",
        ec="black",
        linewidth=1.5,
        length_includes_head=True,
        transform=cbar.ax.transAxes,
        clip_on=False,
    )
    cbar.ax.text(
        x=0.53,
        y=-4,
        s="Elevation\nhigher",
        ha="left",
        va="bottom",
        fontsize=16,
        transform=cbar.ax.transAxes,
    )
    cbar.ax.text(
        x=0.47,
        y=-4,
        s="Elevation\nlower",
        ha="right",
        va="bottom",
        fontsize=16,
        transform=cbar.ax.transAxes,
    )

    # 边框不可见
    ax.spines["geo"].set_visible(False)

    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(output_path)

print("ok")
