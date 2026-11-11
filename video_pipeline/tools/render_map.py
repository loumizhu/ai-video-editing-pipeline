#!/usr/bin/env python3
"""render_map.py - Geographically accurate cartographic map renderer using Natural Earth vector data.
Zero fake geography. Conformal Mercator projection with identical scale for both axes.
Clips land polygons to viewport for high-speed Pillow rasterization.
Computes true great-circle haversine distances (direct straight-line and route sum of legs).
Generates an accurate scale bar from the projection at center latitude.
Supports 6 visually distinct map types:
  1. route_draw: Glowing route path along route legs (straight lines between stops) with animated progress draw-on.
  2. locator_zoom: Wide context map with target reticle matching exact ground extent and zoomed local detail inset panel.
  3. distance_line: Clean direct measurement vector with dimension markers and straight-line readout.
  4. multi_pin_cluster: Bounding-box-fit site cluster, numbered pin badges, and site index legend (no route).
  5. comparison_inset: Primary region canvas + secondary region inset panel at identical 1:1 ground scale.
  6. hidden_connection: Stylised curved connection arc (screen-space curve, not geodesic) with dashed pulsing style, origin/destination badges, and neutral direct distance badge.
Data source: Natural Earth 1:50m Land Vector Data (Public Domain).
"""

import argparse
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    """Loads system fonts or fallback."""
    font_names = ["georgiab.ttf" if bold else "georgia.ttf",
                  "segoeuib.ttf" if bold else "segoeui.ttf",
                  "arialbd.ttf" if bold else "arial.ttf",
                  "trebucbd.ttf" if bold else "trebuc.ttf"]
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")
    for name in font_names:
        p = os.path.join(fonts_dir, name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except IOError:
                continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def haversine_distance(lat1, lon1, lat2, lon2):
    """Computes great-circle distance between two points in miles and km using WGS84 mean radius."""
    R_earth_mi = 3958.7613
    R_earth_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return c * R_earth_mi, c * R_earth_km

def clip_polygon_to_rect(poly_pts, xmin, ymin, xmax, ymax):
    """Sutherland-Hodgman polygon clipping against a rectangular viewport."""
    def clip_edge(pts, edge_idx):
        out = []
        if not pts:
            return out
        for i in range(len(pts)):
            cur = pts[i]
            prev = pts[(i - 1) % len(pts)]

            def inside(p):
                if edge_idx == 0: return p[0] >= xmin
                if edge_idx == 1: return p[0] <= xmax
                if edge_idx == 2: return p[1] >= ymin
                if edge_idx == 3: return p[1] <= ymax
                return True

            def intersect(p1, p2):
                x1, y1 = p1
                x2, y2 = p2
                dx = x2 - x1
                dy = y2 - y1
                if edge_idx == 0:
                    y = y1 + dy * (xmin - x1) / (dx if dx != 0 else 1e-9)
                    return (xmin, y)
                elif edge_idx == 1:
                    y = y1 + dy * (xmax - x1) / (dx if dx != 0 else 1e-9)
                    return (xmax, y)
                elif edge_idx == 2:
                    x = x1 + dx * (ymin - y1) / (dy if dy != 0 else 1e-9)
                    return (x, ymin)
                elif edge_idx == 3:
                    x = x1 + dx * (ymax - y1) / (dy if dy != 0 else 1e-9)
                    return (x, ymax)
                return (x1, y1)

            if inside(cur):
                if not inside(prev):
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(intersect(prev, cur))
        return out

    res = poly_pts
    for edge in range(4):
        res = clip_edge(res, edge)
        if not res:
            break
    return res

class MapProjector:
    """Conformal Mercator projection ensuring true geographic scale k (px/rad) across both axes."""
    def __init__(self, bounds=None, width=1920, height=1080, margin_pct=0.35,
                 center_lon=None, center_lat=None, fixed_scale=None, origin_x=0.0, origin_y=0.0):
        self.width = width
        self.height = height
        self.origin_x = origin_x
        self.origin_y = origin_y

        if fixed_scale is not None and center_lon is not None and center_lat is not None:
            self.scale = fixed_scale
            self.lon0_rad = math.radians(center_lon)
            self.lat0_merc = self._lat_to_merc(center_lat)
            self.center_lat = center_lat
            self.center_lon = center_lon
            self.cx = origin_x + width / 2.0
            self.cy = origin_y + height / 2.0
        else:
            min_lon, min_lat, max_lon, max_lat = bounds
            min_lat = max(min(85.0, min_lat), -85.0)
            max_lat = max(min(85.0, max_lat), -85.0)
            if min_lat > max_lat:
                min_lat, max_lat = max_lat, min_lat
            if min_lon > max_lon:
                min_lon, max_lon = max_lon, min_lon

            x_min = math.radians(min_lon)
            x_max = math.radians(max_lon)
            y_min = self._lat_to_merc(min_lat)
            y_max = self._lat_to_merc(max_lat)

            span_x = x_max - x_min
            span_y = y_max - y_min

            min_span = 0.05  # approx 2.8 degrees
            if span_x < min_span:
                mid_x = (x_min + x_max) / 2.0
                x_min = mid_x - min_span / 2.0
                x_max = mid_x + min_span / 2.0
                span_x = min_span
            if span_y < min_span:
                mid_y = (y_min + y_max) / 2.0
                y_min = mid_y - min_span / 2.0
                y_max = mid_y + min_span / 2.0
                span_y = min_span

            x_min -= span_x * margin_pct
            x_max += span_x * margin_pct
            y_min -= span_y * margin_pct
            y_max += span_y * margin_pct

            total_span_x = x_max - x_min
            total_span_y = y_max - y_min

            scale_x = width / total_span_x
            scale_y = height / total_span_y
            self.scale = min(scale_x, scale_y)

            self.lon0_rad = (x_min + x_max) / 2.0
            self.lat0_merc = (y_min + y_max) / 2.0
            self.cx = origin_x + width / 2.0
            self.cy = origin_y + height / 2.0

            self.center_lat = math.degrees(2.0 * math.atan(math.exp(self.lat0_merc)) - math.pi / 2.0)
            self.center_lon = math.degrees(self.lon0_rad)

        left_lon, top_lat = self.unproject(origin_x, origin_y)
        right_lon, bottom_lat = self.unproject(origin_x + width, origin_y + height)
        self.visible_min_lon = min(left_lon, right_lon)
        self.visible_max_lon = max(left_lon, right_lon)
        self.visible_min_lat = min(bottom_lat, top_lat)
        self.visible_max_lat = max(bottom_lat, top_lat)

    def _lat_to_merc(self, lat):
        """Converts latitude in degrees to Mercator Y in radians."""
        clamped = max(min(lat, 85.0), -85.0)
        rad = math.radians(clamped)
        return math.log(math.tan(math.pi / 4.0 + rad / 2.0))

    def project(self, lon, lat):
        """Converts lon, lat (degrees) to pixel coordinates (x, y) preserving aspect ratio."""
        x_rad = math.radians(lon)
        y_merc = self._lat_to_merc(lat)
        px = self.cx + self.scale * (x_rad - self.lon0_rad)
        py = self.cy - self.scale * (y_merc - self.lat0_merc)
        return px, py

    def unproject(self, px, py):
        """Converts screen pixel (x, y) back to lon, lat (degrees)."""
        x_rad = self.lon0_rad + (px - self.cx) / self.scale
        y_merc = self.lat0_merc - (py - self.cy) / self.scale
        lon = math.degrees(x_rad)
        lat = math.degrees(2.0 * math.atan(math.exp(y_merc)) - math.pi / 2.0)
        return lon, lat

def load_geojson_polygons(geojson_path, projector, clip_rect=None):
    """Loads GeoJSON, filters to visible region, and clips polygon rings to viewport."""
    if not os.path.exists(geojson_path):
        return []

    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    screen_polys = []
    pad = 4.0  # degree search buffer
    min_lon = projector.visible_min_lon - pad
    max_lon = projector.visible_max_lon + pad
    min_lat = projector.visible_min_lat - pad
    max_lat = projector.visible_max_lat + pad

    if clip_rect is not None:
        c_xmin, c_ymin, c_xmax, c_ymax = clip_rect
    else:
        clip_margin = 40.0
        c_xmin, c_ymin = projector.origin_x - clip_margin, projector.origin_y - clip_margin
        c_xmax, c_ymax = projector.origin_x + projector.width + clip_margin, projector.origin_y + projector.height + clip_margin

    for feature in data.get('features', []):
        geom = feature.get('geometry', {})
        gtype = geom.get('type')
        coords = geom.get('coordinates', [])

        polygons = []
        if gtype == 'Polygon':
            polygons = [coords]
        elif gtype == 'MultiPolygon':
            polygons = coords

        for poly in polygons:
            if not poly:
                continue
            ext_ring = poly[0]
            ring_lons = [pt[0] for pt in ext_ring]
            ring_lats = [pt[1] for pt in ext_ring]
            if max(ring_lons) < min_lon or min(ring_lons) > max_lon:
                continue
            if max(ring_lats) < min_lat or min(ring_lats) > max_lat:
                continue

            pts = [projector.project(pt[0], pt[1]) for pt in ext_ring]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if max(xs) < c_xmin or min(xs) > c_xmax or max(ys) < c_ymin or min(ys) > c_ymax:
                continue

            clipped = clip_polygon_to_rect(pts, c_xmin, c_ymin, c_xmax, c_ymax)
            if len(clipped) >= 3:
                screen_polys.append(clipped)

    return screen_polys

def draw_grid_lines(draw, projector, width, height, is_overlay, clip_rect=None):
    """Draws subtle longitude and latitude graticules avoiding footer and title collisions."""
    grid_color = (60, 75, 100, 70) if not is_overlay else (180, 190, 210, 40)
    font = get_font(13)

    ox = projector.origin_x
    oy = projector.origin_y
    vx_max = ox + width
    vy_max = oy + height

    lat_span = projector.visible_max_lat - projector.visible_min_lat
    if lat_span < 4.0:
        lat_step = 1.0
    elif lat_span < 12.0:
        lat_step = 2.0
    else:
        lat_step = 5.0

    start_lat = math.floor(projector.visible_min_lat / lat_step) * lat_step
    curr_lat = start_lat
    while curr_lat <= projector.visible_max_lat + lat_step:
        if -85.0 <= curr_lat <= 85.0:
            _, py = projector.project(projector.center_lon, curr_lat)
            if oy + 30 <= py <= vy_max - 40:
                draw.line([(ox, py), (vx_max, py)], fill=grid_color, width=1)
                if not (py < 180 and ox < 100):
                    label = f"{abs(curr_lat):.0f}°{'N' if curr_lat>=0 else 'S'}"
                    draw.text((ox + 16, py - 16), label, font=font, fill=(130, 145, 170, 160))
        curr_lat += lat_step

    lon_span = projector.visible_max_lon - projector.visible_min_lon
    if lon_span < 4.0:
        lon_step = 1.0
    elif lon_span < 12.0:
        lon_step = 2.0
    else:
        lon_step = 5.0

    start_lon = math.floor(projector.visible_min_lon / lon_step) * lon_step
    curr_lon = start_lon
    while curr_lon <= projector.visible_max_lon + lon_step:
        px, _ = projector.project(curr_lon, projector.center_lat)
        if ox <= px <= vx_max:
            draw.line([(px, oy), (px, vy_max)], fill=grid_color, width=1)
            if px < vx_max - 520 and px > ox + 160:
                label = f"{abs(curr_lon):.0f}°{'E' if curr_lon>=0 else 'W'}"
                draw.text((px + 6, vy_max - 30), label, font=font, fill=(130, 145, 170, 160))
        curr_lon += lon_step

def draw_scale_bar(draw, projector, width, height, bx0=80, by0=None, target_px=220.0, is_inset=False):
    """Draws an accurate cartographic scale bar computed from projection scale at center latitude."""
    R_km = 6371.0088
    phi_rad = math.radians(projector.center_lat)
    km_per_rad = R_km * math.cos(phi_rad)
    km_per_pixel = km_per_rad / projector.scale
    if km_per_pixel <= 0:
        return

    approx_km = target_px * km_per_pixel
    candidate_steps = [2, 5, 10, 20, 25, 50, 75, 100, 150, 200, 250, 300, 500, 1000]
    chosen_km = candidate_steps[0]
    for c in candidate_steps:
        if abs(c - approx_km) < abs(chosen_km - approx_km):
            chosen_km = c

    bar_px = chosen_km / km_per_pixel
    chosen_mi = chosen_km * 0.621371

    if by0 is None:
        by0 = height - 90

    bx1 = bx0 + int(bar_px)
    bmid = (bx0 + bx1) / 2

    font_tick = get_font(11 if is_inset else 12, bold=True)
    font_sub = get_font(9 if is_inset else 11)

    km_text = f"{chosen_km} km"
    km_bbox = font_tick.getbbox(km_text)
    km_w = km_bbox[2] - km_bbox[0]

    box_x1 = max(bx1 + 36, bx1 + km_w + 16)
    draw.rounded_rectangle([bx0 - 18, by0 - 24, box_x1, by0 + 36], radius=6,
                           fill=(12, 16, 24, 220), outline=(212, 175, 55, 180), width=1)

    bar_color = (255, 235, 130, 255)
    bar_y = by0 + 10
    draw.line([(bx0, bar_y), (bx1, bar_y)], fill=bar_color, width=3)
    draw.line([(bx0, bar_y - 6), (bx0, bar_y + 6)], fill=bar_color, width=2)
    draw.line([(bmid, bar_y - 4), (bmid, bar_y + 4)], fill=bar_color, width=1)
    draw.line([(bx1, bar_y - 6), (bx1, bar_y + 6)], fill=bar_color, width=2)

    draw.text((bx0 - 4, bar_y - 20), "0", font=font_tick, fill=bar_color)
    draw.text((bx1 - km_w / 2, bar_y - 20), km_text, font=font_tick, fill=bar_color)
    draw.text((bx0, bar_y + 10), f"SCALE ({chosen_mi:.0f} mi)", font=font_sub, fill=(180, 195, 215, 220))

def place_labels_avoiding_collision(draw, points_projected, font):
    """Positions pin labels staying adjacent to their own pin and repelling neighbor pins."""
    placed_boxes = []
    labels_to_render = []

    for pt in points_projected:
        px, py, label = pt['x'], pt['y'], pt['name']
        bbox = font.getbbox(label)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]

        pad_x, pad_y = 12, 6
        box_w = lw + pad_x * 2
        box_h = lh + pad_y * 2

        neighbor_dx, neighbor_dy = 0.0, 0.0
        has_neighbor = False
        for other in points_projected:
            if other is pt:
                continue
            dist = math.hypot(other['x'] - px, other['y'] - py)
            if dist < 160.0:
                neighbor_dx += (other['x'] - px)
                neighbor_dy += (other['y'] - py)
                has_neighbor = True

        candidates = [
            ('right', px + 18, py - box_h / 2),
            ('left', px - box_w - 18, py - box_h / 2),
            ('top', px - box_w / 2, py - box_h - 22),
            ('bottom', px - box_w / 2, py + 22)
        ]

        if has_neighbor:
            def score_candidate(cand):
                dir_name, cx, cy = cand
                mid_x = cx + box_w / 2.0
                mid_y = cy + box_h / 2.0
                vec_x = mid_x - px
                vec_y = mid_y - py
                dot = vec_x * neighbor_dx + vec_y * neighbor_dy
                return dot
            candidates.sort(key=score_candidate)

        best_pos = None
        for dir_name, cx, cy in candidates:
            cand_rect = [cx, cy, cx + box_w, cy + box_h]
            collision = False
            for pb in placed_boxes:
                if not (cand_rect[2] < pb[0] or cand_rect[0] > pb[2] or cand_rect[3] < pb[1] or cand_rect[1] > pb[3]):
                    collision = True
                    break
            for other in points_projected:
                if other is pt:
                    continue
                if (cand_rect[0] - 8 <= other['x'] <= cand_rect[2] + 8 and
                    cand_rect[1] - 8 <= other['y'] <= cand_rect[3] + 8):
                    collision = True
                    break

            if not collision:
                best_pos = (cx, cy, cand_rect)
                break

        if best_pos is None:
            dir_name, cx, cy = candidates[0]
            cy += 24 * len(placed_boxes)
            best_pos = (cx, cy, [cx, cy, cx + box_w, cy + box_h])

        placed_boxes.append(best_pos[2])
        labels_to_render.append((pt, best_pos[0], best_pos[1], box_w, box_h, lw, lh))

    return labels_to_render

def render_map(title, subtitle, points_raw, distance_override=None,
               progress=1.0, map_type="route_draw", is_overlay=False,
               illustrative=False, data_dir=None):
    """Renders map image with real Natural Earth vector geometry and conformal projection."""
    width, height = 1920, 1080

    points = []
    lats, lons = [], []
    for item in points_raw.split(';'):
        item = item.strip()
        if not item:
            continue
        parts = item.split(',', 2)
        if len(parts) >= 3:
            lat, lon, name = float(parts[0]), float(parts[1]), parts[2].strip()
            points.append({"lat": lat, "lon": lon, "name": name})
            lats.append(lat)
            lons.append(lon)

    if not points:
        raise ValueError("At least one geographical point (lat,lon,name) required.")

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    geojson_path = os.path.join(data_dir, 'ne_50m_land.geojson')

    land_fill = (26, 32, 45, 255) if not is_overlay else (20, 26, 38, 200)
    land_outline = (55, 70, 95, 255) if not is_overlay else (75, 95, 125, 220)

    if is_overlay:
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    else:
        img = Image.new('RGBA', (width, height), (15, 18, 26, 255))
    draw = ImageDraw.Draw(img)

    # -------------------------------------------------------------
    # 1. SPECIAL MAP TYPE: comparison_inset
    # -------------------------------------------------------------
    if map_type == "comparison_inset" and len(points) >= 2:
        pt1 = points[0]
        pt2 = points[1] if len(points) == 2 else points[-1]

        main_margin = 0.40
        main_bounds = (pt1['lon'] - 0.9, pt1['lat'] - 0.55, pt1['lon'] + 0.9, pt1['lat'] + 0.55)
        projector = MapProjector(main_bounds, width, height, margin_pct=main_margin)

        draw_grid_lines(draw, projector, width, height, is_overlay)
        polys = load_geojson_polygons(geojson_path, projector)
        for poly_pts in polys:
            draw.polygon(poly_pts, fill=land_fill, outline=land_outline)

        px1, py1 = projector.project(pt1['lon'], pt1['lat'])
        proj_pts1 = [{"x": px1, "y": py1, "lat": pt1['lat'], "lon": pt1['lon'], "name": pt1['name']}]
        pin_font = get_font(20, bold=True)
        draw.ellipse([px1 - 14, py1 - 14, px1 + 14, py1 + 14], fill=(212, 175, 55, 70))
        draw.ellipse([px1 - 7, py1 - 7, px1 + 7, py1 + 7], fill=(255, 240, 140, 255), outline=(15, 18, 26, 255), width=2)
        draw.ellipse([px1 - 2, py1 - 2, px1 + 2, py1 + 2], fill=(200, 30, 30, 255))

        labels1 = place_labels_avoiding_collision(draw, proj_pts1, pin_font)
        for pt, bx, by, bw, bh, lw, lh in labels1:
            draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill=(12, 16, 24, 220), outline=(212, 175, 55, 210), width=1)
            draw.text((bx + (bw - lw) / 2, by + (bh - lh) / 2 - 2), pt['name'], font=pin_font, fill=(245, 242, 235, 255))
            draw.line([(px1, py1), (bx if bx > px1 else bx + bw, by + bh / 2)], fill=(212, 175, 55, 150), width=1)

        draw_scale_bar(draw, projector, width, height, bx0=80)

        # SECONDARY INSET: Identical ground scale k
        ix0, iy0, iw, ih = 1240, 60, 620, 440
        inset_rect = [ix0, iy0, ix0 + iw, iy0 + ih]
        draw.rounded_rectangle(inset_rect, radius=10, fill=(10, 14, 22, 245), outline=None)

        inset_proj = MapProjector(width=iw, height=ih, center_lon=pt2['lon'], center_lat=pt2['lat'],
                                  fixed_scale=projector.scale, origin_x=ix0, origin_y=iy0)

        inset_polys = load_geojson_polygons(geojson_path, inset_proj, clip_rect=inset_rect)
        for poly_pts in inset_polys:
            draw.polygon(poly_pts, fill=(32, 40, 56, 255), outline=(80, 105, 140, 255))

        px2, py2 = inset_proj.project(pt2['lon'], pt2['lat'])
        draw.ellipse([px2 - 14, py2 - 14, px2 + 14, py2 + 14], fill=(100, 220, 255, 80))
        draw.ellipse([px2 - 7, py2 - 7, px2 + 7, py2 + 7], fill=(140, 240, 255, 255), outline=(15, 18, 26, 255), width=2)
        draw.ellipse([px2 - 2, py2 - 2, px2 + 2, py2 + 2], fill=(0, 140, 220, 255))

        lbl_font = get_font(18, bold=True)
        lbl_text = pt2['name']
        lbbox = lbl_font.getbbox(lbl_text)
        lw2, lh2 = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
        lbx, lby = px2 - lw2 / 2 - 10, py2 + 18
        draw.rounded_rectangle([lbx, lby, lbx + lw2 + 20, lby + lh2 + 10], radius=5, fill=(12, 16, 24, 225), outline=(100, 220, 255, 220), width=1)
        draw.text((lbx + 10, lby + 4), lbl_text, font=lbl_font, fill=(245, 242, 235, 255))

        draw_scale_bar(draw, inset_proj, width, height, bx0=ix0 + 24, by0=iy0 + ih - 45, target_px=140.0, is_inset=True)

        in_hdr_font = get_font(15, bold=True)
        draw.rounded_rectangle([ix0 + 16, iy0 + 14, ix0 + iw - 16, iy0 + 44], radius=5, fill=(15, 20, 30, 230), outline=(212, 175, 55, 180), width=1)
        draw.text((ix0 + 26, iy0 + 20), "SCALE COMPARISON (1:1 GROUND EQUIVALENCE)", font=in_hdr_font, fill=(255, 235, 130, 255))

        note_font = get_font(11, bold=True)
        draw.rounded_rectangle([ix0 + iw - 220, iy0 + ih - 36, ix0 + iw - 18, iy0 + ih - 14], radius=4, fill=(15, 20, 30, 230), outline=(100, 200, 240, 160), width=1)
        draw.text((ix0 + iw - 212, iy0 + ih - 32), "1:1 IDENTICAL SCALE RATIO", font=note_font, fill=(160, 220, 255, 240))

        # Redraw inset border outline LAST so land polygons never overpaint the border
        draw.rounded_rectangle(inset_rect, radius=10, fill=None, outline=(212, 175, 55, 240), width=2)

    # -------------------------------------------------------------
    # 2. SPECIAL MAP TYPE: locator_zoom
    # -------------------------------------------------------------
    elif map_type == "locator_zoom":
        target_pt = points[0]
        ctx_margin = 1.35
        projector = MapProjector((min_lon, min_lat, max_lon, max_lat), width, height, margin_pct=ctx_margin)

        draw_grid_lines(draw, projector, width, height, is_overlay)
        polys = load_geojson_polygons(geojson_path, projector)
        for poly_pts in polys:
            draw.polygon(poly_pts, fill=land_fill, outline=land_outline)

        draw_scale_bar(draw, projector, width, height, bx0=80)

        # Zoomed Local Detail Inset Panel (Top Right)
        ix0, iy0, iw, ih = 1240, 60, 620, 440
        inset_rect = [ix0, iy0, ix0 + iw, iy0 + ih]

        tight_bounds = (target_pt['lon'] - 0.28, target_pt['lat'] - 0.16, target_pt['lon'] + 0.28, target_pt['lat'] + 0.16)
        inset_proj = MapProjector(tight_bounds, width=iw, height=ih, margin_pct=0.15, origin_x=ix0, origin_y=iy0)

        # Reticle derived directly from inset panel's exact ground extent unprojected from inset_proj
        in_lon_min, in_lat_max = inset_proj.unproject(ix0, iy0)
        in_lon_max, in_lat_min = inset_proj.unproject(ix0 + iw, iy0 + ih)

        # Project inset corners onto the wide context map to get exact reticle rectangle
        rx0, ry0 = projector.project(in_lon_min, in_lat_max)
        rx1, ry1 = projector.project(in_lon_max, in_lat_min)
        rx_min, rx_max = min(rx0, rx1), max(rx0, rx1)
        ry_min, ry_max = min(ry0, ry1), max(ry0, ry1)

        # Highlighted zoom target reticle on main map matching exact inset ground extent
        draw.rectangle([rx_min, ry_min, rx_max, ry_max], outline=(255, 235, 130, 240), width=2)

        # Corner tick brackets on reticle
        bracket_len = max(6, min(16, int((rx_max - rx_min) / 4)))
        for cx, cy in [(rx_min, ry_min), (rx_max, ry_min), (rx_min, ry_max), (rx_max, ry_max)]:
            sx = 1 if cx == rx_min else -1
            sy = 1 if cy == ry_min else -1
            draw.line([(cx, cy), (cx + sx * bracket_len, cy)], fill=(212, 175, 55, 255), width=3)
            draw.line([(cx, cy), (cx, cy + sy * bracket_len)], fill=(212, 175, 55, 255), width=3)

        # Center target pin on context map
        tx, ty = projector.project(target_pt['lon'], target_pt['lat'])
        draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(255, 240, 140, 255), outline=(15, 18, 26, 255), width=2)

        # Connector lines from reticle to inset panel
        draw.line([(rx_max, ry_min), (ix0, iy0 + 60)], fill=(212, 175, 55, 140), width=1)
        draw.line([(rx_max, ry_max), (ix0, iy0 + ih - 60)], fill=(212, 175, 55, 140), width=1)

        # Inset background fill
        draw.rounded_rectangle(inset_rect, radius=10, fill=(10, 14, 22, 245), outline=None)

        inset_polys = load_geojson_polygons(geojson_path, inset_proj, clip_rect=inset_rect)
        for poly_pts in inset_polys:
            draw.polygon(poly_pts, fill=(35, 44, 60, 255), outline=(85, 110, 145, 255))

        # Detailed target pin inside inset
        ipx, ipy = inset_proj.project(target_pt['lon'], target_pt['lat'])
        draw.ellipse([ipx - 22, ipy - 22, ipx + 22, ipy + 22], fill=(212, 175, 55, 60))
        draw.ellipse([ipx - 12, ipy - 12, ipx + 12, ipy + 12], fill=(255, 235, 130, 255), outline=(15, 18, 26, 255), width=2)
        draw.ellipse([ipx - 4, ipy - 4, ipx + 4, ipy + 4], fill=(200, 30, 30, 255))

        lbl_font = get_font(20, bold=True)
        lbl_text = target_pt['name']
        lbbox = lbl_font.getbbox(lbl_text)
        lw_t, lh_t = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
        lbx, lby = ipx - lw_t / 2 - 14, ipy + 24
        draw.rounded_rectangle([lbx, lby, lbx + lw_t + 28, lby + lh_t + 12], radius=6, fill=(12, 16, 24, 230), outline=(212, 175, 55, 220), width=1)
        draw.text((lbx + 14, lby + 4), lbl_text, font=lbl_font, fill=(245, 242, 235, 255))

        # Inset scale bar
        draw_scale_bar(draw, inset_proj, width, height, bx0=ix0 + 24, by0=iy0 + ih - 45, target_px=140.0, is_inset=True)

        # Inset header
        in_hdr_font = get_font(15, bold=True)
        draw.rounded_rectangle([ix0 + 16, iy0 + 14, ix0 + iw - 16, iy0 + 44], radius=5, fill=(15, 20, 30, 230), outline=(212, 175, 55, 180), width=1)
        draw.text((ix0 + 26, iy0 + 20), "LOCAL DETAIL // HIGH-RESOLUTION ZOOM INSET", font=in_hdr_font, fill=(255, 235, 130, 255))

        # Draw inset frame outline LAST so land polygons never overpaint the border
        draw.rounded_rectangle(inset_rect, radius=10, fill=None, outline=(212, 175, 55, 240), width=2)

    # -------------------------------------------------------------
    # 3. STANDARD MAP CANVAS: route_draw, distance_line, multi_pin_cluster, hidden_connection
    # -------------------------------------------------------------
    else:
        projector = MapProjector((min_lon, min_lat, max_lon, max_lat), width, height, margin_pct=0.35)

        draw_grid_lines(draw, projector, width, height, is_overlay)
        polys = load_geojson_polygons(geojson_path, projector)
        for poly_pts in polys:
            draw.polygon(poly_pts, fill=land_fill, outline=land_outline)

        projected_points = []
        for pt in points:
            px, py = projector.project(pt['lon'], pt['lat'])
            projected_points.append({"x": px, "y": py, "lat": pt['lat'], "lon": pt['lon'], "name": pt['name']})

        dir_mi, dir_km = haversine_distance(points[0]['lat'], points[0]['lon'], points[-1]['lat'], points[-1]['lon'])
        total_legs_mi, total_legs_km = 0.0, 0.0
        for i in range(len(points) - 1):
            d_mi, d_km = haversine_distance(points[i]['lat'], points[i]['lon'], points[i+1]['lat'], points[i+1]['lon'])
            total_legs_mi += d_mi
            total_legs_km += d_km

        # -----------------
        # MAP TYPE: hidden_connection (curved dashed glowing arc)
        # -----------------
        if map_type == "hidden_connection" and len(projected_points) >= 2:
            p0 = projected_points[0]
            p1 = projected_points[-1]
            steps = 90
            arc_pts = []
            for s in range(steps + 1):
                t = s / steps
                curv = math.sin(t * math.pi) * 65.0
                ix = p0['x'] + (p1['x'] - p0['x']) * t
                iy = p0['y'] + (p1['y'] - p0['y']) * t - curv
                arc_pts.append((ix, iy))

            visible_count = max(2, int(len(arc_pts) * max(0.01, min(1.0, progress))))
            visible_path = arc_pts[:visible_count]

            draw.line(visible_path, fill=(0, 190, 255, 90), width=9)
            for i in range(len(visible_path) - 1):
                if (i // 3) % 2 == 0:
                    draw.line([visible_path[i], visible_path[i+1]], fill=(120, 240, 255, 255), width=4)

            badge_font = get_font(14, bold=True)
            for pt, code, color, border_color in [(p0, "A", (0, 180, 240, 255), (140, 240, 255, 255)),
                                                 (p1, "B", (212, 175, 55, 255), (255, 240, 140, 255))]:
                epx, epy = pt['x'], pt['y']
                draw.ellipse([epx - 16, epy - 16, epx + 16, epy + 16], fill=(12, 16, 24, 230), outline=border_color, width=2)
                draw.text((epx - 5, epy - 9), code, font=badge_font, fill=color)

        # -----------------
        # MAP TYPE: route_draw (route legs, straight lines between stops)
        # -----------------
        elif map_type == "route_draw" and len(projected_points) >= 2:
            all_path_pts = []
            for i in range(len(projected_points) - 1):
                p0 = projected_points[i]
                p1 = projected_points[i+1]
                steps = 50
                for s in range(steps + 1):
                    t = s / steps
                    curv = math.sin(t * math.pi) * 12.0
                    ix = p0['x'] + (p1['x'] - p0['x']) * t
                    iy = p0['y'] + (p1['y'] - p0['y']) * t - curv
                    all_path_pts.append((ix, iy))

            visible_count = max(2, int(len(all_path_pts) * max(0.01, min(1.0, progress))))
            visible_path = all_path_pts[:visible_count]

            draw.line(visible_path, fill=(212, 175, 55, 90), width=8)
            draw.line(visible_path, fill=(255, 230, 110, 255), width=4)

        # -----------------
        # MAP TYPE: distance_line (straight measurement line)
        # -----------------
        elif map_type == "distance_line" and len(projected_points) >= 2:
            p0 = projected_points[0]
            p1 = projected_points[-1]
            draw.line([(p0['x'], p0['y']), (p1['x'], p1['y'])], fill=(212, 175, 55, 90), width=6)
            draw.line([(p0['x'], p0['y']), (p1['x'], p1['y'])], fill=(255, 235, 130, 240), width=3)
            for p in (p0, p1):
                draw.line([(p['x'] - 12, p['y'] - 12), (p['x'] + 12, p['y'] + 12)], fill=(255, 235, 130, 255), width=2)
                draw.line([(p['x'] - 12, p['y'] + 12), (p['x'] + 12, p['y'] - 12)], fill=(255, 235, 130, 255), width=2)

        # -----------------
        # PINS & LABELS: multi_pin_cluster vs standard
        # -----------------
        pin_font = get_font(20, bold=True)
        if map_type == "multi_pin_cluster":
            num_font = get_font(15, bold=True)
            for idx, pt in enumerate(projected_points, 1):
                px, py = pt['x'], pt['y']
                draw.ellipse([px - 16, py - 16, px + 16, py + 16], fill=(212, 175, 55, 230), outline=(15, 18, 26, 255), width=2)
                draw.text((px - (4 if idx < 10 else 8), py - 9), str(idx), font=num_font, fill=(15, 18, 26, 255))

            lx0 = 1360
            ly0 = 60
            lw = 500
            lh = 50 + len(projected_points) * 44
            draw.rounded_rectangle([lx0, ly0, lx0 + lw, ly0 + lh], radius=8,
                                   fill=(12, 16, 24, 235), outline=(212, 175, 55, 220), width=2)

            leg_title_font = get_font(15, bold=True)
            draw.text((lx0 + 20, ly0 + 16), "SITE INDEX & CLUSTER LEGEND", font=leg_title_font, fill=(255, 235, 130, 255))
            draw.line([(lx0 + 20, ly0 + 40), (lx0 + lw - 20, ly0 + 40)], fill=(55, 70, 95, 200), width=1)

            entry_font = get_font(14, bold=True)
            coord_font = get_font(12, bold=False)
            for idx, pt in enumerate(projected_points, 1):
                ey = ly0 + 50 + (idx - 1) * 44
                draw.ellipse([lx0 + 20, ey + 2, lx0 + 44, ey + 26], fill=(212, 175, 55, 230), outline=(15, 18, 26, 255), width=1)
                draw.text((lx0 + 27, ey + 5), str(idx), font=get_font(12, bold=True), fill=(15, 18, 26, 255))
                draw.text((lx0 + 54, ey + 2), pt['name'], font=entry_font, fill=(245, 242, 235, 255))
                lat_str = f"{abs(pt['lat']):.2f}°{'N' if pt['lat']>=0 else 'S'}"
                lon_str = f"{abs(pt['lon']):.2f}°{'E' if pt['lon']>=0 else 'W'}"
                draw.text((lx0 + 54, ey + 22), f"{lat_str}, {lon_str}", font=coord_font, fill=(160, 185, 215, 220))

            labels = place_labels_avoiding_collision(draw, projected_points, pin_font)
            for pt, bx, by, bw, bh, lw_b, lh_b in labels:
                draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill=(12, 16, 24, 220), outline=(212, 175, 55, 210), width=1)
                draw.text((bx + (bw - lw_b) / 2, by + (bh - lh_b) / 2 - 2), pt['name'], font=pin_font, fill=(245, 242, 235, 255))
                draw.line([(pt['x'], pt['y']), (bx if bx > pt['x'] else bx + bw, by + bh / 2)], fill=(212, 175, 55, 150), width=1)

        else:
            for pt in projected_points:
                px, py = pt['x'], pt['y']
                draw.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(212, 175, 55, 70))
                draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 240, 140, 255), outline=(15, 18, 26, 255), width=2)
                draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(200, 30, 30, 255))

            labels = place_labels_avoiding_collision(draw, projected_points, pin_font)
            for pt, bx, by, bw, bh, lw_b, lh_b in labels:
                draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill=(12, 16, 24, 220), outline=(212, 175, 55, 210), width=1)
                draw.text((bx + (bw - lw_b) / 2, by + (bh - lh_b) / 2 - 2), pt['name'], font=pin_font, fill=(245, 242, 235, 255))
                draw.line([(pt['x'], pt['y']), (bx if bx > pt['x'] else bx + bw, by + bh / 2)], fill=(212, 175, 55, 150), width=1)

        draw_scale_bar(draw, projector, width, height)

        if len(points) >= 2 and map_type in ("route_draw", "distance_line", "hidden_connection"):
            if progress >= 0.20:
                dist_factor = 1.0 if progress >= 1.0 else (progress - 0.20) / 0.80
                curr_dir_mi = dir_mi * dist_factor
                curr_dir_km = dir_km * dist_factor
                curr_total_legs_mi = total_legs_mi * dist_factor
                curr_total_legs_km = total_legs_km * dist_factor

                dist_font_main = get_font(20, bold=True)
                dist_font_sub = get_font(16, bold=False)

                if map_type == "hidden_connection":
                    line1 = f"CONNECTION // DIRECT DISTANCE: {curr_dir_mi:.1f} MILES ({curr_dir_km:.1f} KM)"
                    bb1 = dist_font_main.getbbox(line1)
                    w1 = bb1[2] - bb1[0]
                    badge_w = w1 + 48
                    badge_h = 48
                    dx0 = (width - badge_w) / 2
                    dy0 = height - 100
                    draw.rounded_rectangle([dx0, dy0, dx0 + badge_w, dy0 + badge_h], radius=8,
                                           fill=(12, 16, 24, 235), outline=(0, 190, 255, 230), width=2)
                    draw.text((dx0 + 24, dy0 + 12), line1, font=dist_font_main, fill=(120, 240, 255, 255))
                elif len(points) >= 3:
                    line1 = f"DIRECT A->Z: {curr_dir_mi:.1f} MILES ({curr_dir_km:.1f} KM)"
                    line2 = f"ROUTE LENGTH (SUM OF LEGS): {curr_total_legs_mi:.1f} MILES ({curr_total_legs_km:.1f} KM)"
                    bb1 = dist_font_main.getbbox(line1)
                    bb2 = dist_font_sub.getbbox(line2)
                    w1 = bb1[2] - bb1[0]
                    w2 = bb2[2] - bb2[0]
                    badge_w = max(w1, w2) + 48
                    badge_h = 70
                    dx0 = (width - badge_w) / 2
                    dy0 = height - 120
                    draw.rounded_rectangle([dx0, dy0, dx0 + badge_w, dy0 + badge_h], radius=8,
                                           fill=(12, 16, 24, 230), outline=(212, 175, 55, 230), width=2)
                    draw.text((dx0 + (badge_w - w1) / 2, dy0 + 10), line1, font=dist_font_main, fill=(255, 235, 130, 255))
                    draw.text((dx0 + (badge_w - w2) / 2, dy0 + 38), line2, font=dist_font_sub, fill=(210, 225, 245, 240))
                else:
                    line1 = f"DIRECT STRAIGHT-LINE: {curr_dir_mi:.1f} MILES ({curr_dir_km:.1f} KM)"
                    bb1 = dist_font_main.getbbox(line1)
                    w1 = bb1[2] - bb1[0]
                    badge_w = w1 + 48
                    badge_h = 48
                    dx0 = (width - badge_w) / 2
                    dy0 = height - 100
                    draw.rounded_rectangle([dx0, dy0, dx0 + badge_w, dy0 + badge_h], radius=8,
                                           fill=(12, 16, 24, 230), outline=(212, 175, 55, 230), width=2)
                    draw.text((dx0 + 24, dy0 + 12), line1, font=dist_font_main, fill=(255, 235, 130, 255))

    # -------------------------------------------------------------
    # Universal Frame Elements (Title, Attribution, Watermark)
    # -------------------------------------------------------------
    header_font = get_font(34, bold=True)
    sub_font = get_font(20, bold=False)
    draw.rounded_rectangle([60, 50, 680, 150], radius=8, fill=(10, 14, 22, 220), outline=(212, 175, 55, 220), width=2)
    draw.text((80, 65), title, font=header_font, fill=(245, 242, 235, 255))
    draw.text((82, 108), subtitle, font=sub_font, fill=(212, 175, 55, 240))

    attr_font = get_font(13, bold=False)
    attr_text = "Cartography: Natural Earth 1:50m Vector Data (Public Domain)"
    abox = attr_font.getbbox(attr_text)
    aw = abox[2] - abox[0]
    ax0 = width - aw - 36
    ay0 = height - 42
    draw.rounded_rectangle([ax0 - 12, ay0 - 6, width - 20, height - 14], radius=6,
                           fill=(10, 14, 22, 210), outline=(55, 70, 95, 200), width=1)
    draw.text((ax0, ay0), attr_text, font=attr_font, fill=(160, 175, 195, 220))

    if illustrative:
        wm_font = get_font(18, bold=True)
        wm_text = "SAMPLE // ILLUSTRATIVE"
        wbox = wm_font.getbbox(wm_text)
        ww = wbox[2] - wbox[0]
        wx0 = width - ww - 50
        wy0 = 50
        draw.rounded_rectangle([wx0 - 14, wy0 - 8, width - 24, wy0 + 32], radius=6,
                               fill=(15, 18, 24, 230), outline=(212, 175, 55, 230), width=2)
        draw.text((wx0, wy0), wm_text, font=wm_font, fill=(255, 235, 130, 255))

    return img

def main():
    parser = argparse.ArgumentParser(description="Render geographically accurate cartographic maps")
    parser.add_argument('--title', default="GEOGRAPHIC RECORD", help="Map title")
    parser.add_argument('--subtitle', default="Scale & Locational Analysis", help="Map subtitle")
    parser.add_argument('--points', required=True, help="Semicolon-separated lat,lon,name list")
    parser.add_argument('--type', default="route_draw", choices=["route_draw", "locator_zoom", "distance_line", "multi_pin_cluster", "comparison_inset", "hidden_connection"], help="Map type")
    parser.add_argument('--progress', type=float, default=1.0, help="Route progress (0.0 to 1.0)")
    parser.add_argument('--frames', type=int, default=0, help="If > 0, renders animated PNG frame sequence")
    parser.add_argument('--alpha-overlay', action='store_true', default=False, help="Render transparent overlay for V3/V4")
    parser.add_argument('--illustrative', action='store_true', default=False, help="Add illustrative sample watermark")
    parser.add_argument('--data-dir', default=None, help="Path to directory containing ne_50m_land.geojson")
    parser.add_argument('--out', required=True, help="Output PNG file or directory for frame sequence")
    args = parser.parse_args()

    if args.frames > 0:
        os.makedirs(args.out, exist_ok=True)
        print(f"Rendering {args.frames} animated route frames to {args.out}...")
        for frame_idx in range(args.frames):
            prog = (frame_idx + 1) / args.frames
            frame_img = render_map(
                title=args.title, subtitle=args.subtitle,
                points_raw=args.points, progress=prog,
                map_type=args.type, is_overlay=args.alpha_overlay,
                illustrative=args.illustrative, data_dir=args.data_dir
            )
            frame_path = os.path.join(args.out, f"frame_{frame_idx:04d}.png")
            frame_img.save(frame_path, 'PNG')
        print(f"Finished rendering {args.frames} frames.")
    else:
        img = render_map(
            title=args.title, subtitle=args.subtitle,
            points_raw=args.points, progress=args.progress,
            map_type=args.type, is_overlay=args.alpha_overlay,
            illustrative=args.illustrative, data_dir=args.data_dir
        )
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        img.save(args.out, 'PNG')
        print(f"Rendered map to {args.out} ({img.size[0]}x{img.size[1]} RGBA, alpha_overlay={args.alpha_overlay})")

if __name__ == '__main__':
    main()
