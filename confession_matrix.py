import math
import random
import pygame
import sys
from pygame.math import Vector2


WIDTH, HEIGHT = 1000, 1000
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
NUM_PARTICLES = 10000
T_MORPH_DURATION = 3.5
T_CHAOS_DURATION = 2.5

# 1. 开场快慢参数
FADE_IN_DURATION = 1.0 # 淡入时长
LORENZ_AUTO_TRANSITION = 4.0 # 洛伦兹自动转爱心的时长
LORENZ_MOVE_SPEED = 0.009 # 蝴蝶运动速度

# 2. 心跳核心参数（由慢到快）
HEART_RATE_INIT = 0.6 # 初始慢跳频率（数值越小跳的越慢）
HEART_RATE_MAX = 2.5 # 最高快跳频率（数值越大跳的越快）
HEART_ACCEL_SPEED = 0.2 # 心跳加速速度（数值越大加速越快）
HEART_AMP_INIT = 1.0 # 初始跳动幅度
HEART_AMP_MAX = 2.5 # 最高跳动幅度（跳的越快，幅度越大）

# 3. 循环切换的文字列表（文字阶段按Tab自动轮播）
TEXT_LIST = [ "hey", 'hello',"hi",'bye']
# ======================================================

# --- 按Tab循环切换 ---
# 1. 初始色板：蓝冰系（开场默认）
PALETTE_RED_GOLD = [(180, 15, 25), (255, 40, 50), (255, 160, 60), (255, 215, 120)]
# 2. 第二阶：热烈大红+粉色系（爱心阶段按切换，氛围感拉满）
PALETTE_HOT_RED_PINK = [(120, 0, 20), (220, 0, 40), (255, 60, 120), (255, 180, 220)]
# 3. 第三阶：蓝白冰蓝系
PALETTE_ICE_BLUE = [(220, 240, 255), (140, 210, 255), (50, 150, 230), (10, 70, 130)]
# 切换顺序：红金 → 大红粉 → 蓝白 → 循环
PALETTES = [PALETTE_RED_GOLD, PALETTE_HOT_RED_PINK, PALETTE_ICE_BLUE]

# --- 洛伦兹吸引子核心参数 ---
LORENZ_SIGMA = 10.0
LORENZ_RHO = 28.0
LORENZ_BETA = 8.0 / 3.0
LORENZ_SCALE = 15


class Particle:
def __init__(self):
# 洛伦兹吸引子预迭代（零抖动核心）
self.lorenz_x = random.uniform(-15, 15)
self.lorenz_y = random.uniform(-15, 15)
self.lorenz_z = random.uniform(0, 40)

# 预迭代1000步，彻底杜绝初始扎堆
for _ in range(1000):
dx = LORENZ_SIGMA * (self.lorenz_y - self.lorenz_x) * LORENZ_MOVE_SPEED
dy = (self.lorenz_x * (LORENZ_RHO - self.lorenz_z) - self.lorenz_y) * LORENZ_MOVE_SPEED
dz = (self.lorenz_x * self.lorenz_y - LORENZ_BETA * self.lorenz_z) * LORENZ_MOVE_SPEED
self.lorenz_x += dx
self.lorenz_y += dy
self.lorenz_z += dz

# 初始坐标直接映射蝴蝶轨迹，零跳变
self.x = CENTER_X + self.lorenz_x * LORENZ_SCALE
self.y = CENTER_Y + self.lorenz_y * LORENZ_SCALE

# 形态基准坐标
self.random_base_x = random.uniform(0, WIDTH)
self.random_base_y = random.uniform(0, HEIGHT)
self.heart_base_x, self.heart_base_y, self.heart_base_z = 0, 0, 0
self.text_base_x, self.text_base_y = CENTER_X, CENTER_Y

self.vx, self.vy = 0, 0
self.size = random.uniform(1.0, 2.0)
self.color_idx = random.randint(0, 3)


# --- 爱心拓扑方程 ---
def heart_function(t):
x = 16 * (math.sin(t) ** 3)
y = -(15 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
return x, y


# --- 高清文字采样引擎 ---
def get_text_points_autoscale(text, width, height, num_points):
possible_fonts = ["simhei", "microsoftyahei", "notosanscjk", "arialunicode", "none"]
font = None
test_size = 600

while test_size > 20:
found_font = None
for font_name in possible_fonts:
try:
if font_name == "none":
found_font = pygame.font.Font(None, test_size)
else:
found_font = pygame.font.SysFont(font_name, test_size, bold=True)
if found_font.size(text)[0] > 0: break
except:
continue

if found_font:
test_w, test_h = found_font.size(text)
if test_w < width * 0.92 and test_h < height * 0.92:
font = found_font
break
test_size -= 10

if not font: font = pygame.font.Font(None, 200)

text_surface = font.render(text, True, (255, 255, 255))
text_rect = text_surface.get_rect(center=(width // 2, height // 2))

valid_points = []
step_x, step_y = 1, 1
for x in range(0, text_surface.get_width(), step_x):
for y in range(0, text_surface.get_height(), step_y):
if text_surface.get_at((x, y))[3] > 128:
valid_points.append((x + text_rect.x, y + text_rect.y))

if not valid_points: return [(width // 2, height // 2)] * num_points

sampled_points = []
if len(valid_points) >= num_points:
sampled_points = random.sample(valid_points, num_points)
else:
sampled_points = valid_points * (num_points // len(valid_points) + 1)
sampled_points = sampled_points[:num_points]
random.shuffle(sampled_points)

return sampled_points


# --- 3D空间旋转引擎 ---
def rotate_3d(x, y, z, angle_y, angle_x):
cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
x1, z1 = x * cos_y - z * sin_y, x * sin_y + z * cos_y
cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)
y1, z2 = y * cos_x - z1 * sin_x, y * sin_x + z1 * cos_x
return x1, y1, z2


def main():
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Confession Matrix v9.5 | 切换:Tab | 流程:空格 | 重置:1")
clock = pygame.time.Clock()

trail_surface = pygame.Surface((WIDTH, HEIGHT))
trail_surface.set_alpha(25)
trail_surface.fill((0, 0, 0))

# ========== ==========
current_text_index = 0
current_text = TEXT_LIST[current_text_index]
particles = [Particle() for _ in range(NUM_PARTICLES)]
text_points = get_text_points_autoscale(current_text, WIDTH, HEIGHT, NUM_PARTICLES)

# 初始化爱心基准坐标
for i, p in enumerate(particles):
t = random.uniform(0, 2 * math.pi)
hx, hy = heart_function(t)

if random.random() < 0.85:
diffusion = random.uniform(0.96, 1.0)
noise_z = random.gauss(0, 1.0)
else:
diffusion = random.uniform(0.1, 0.9)
noise_z = random.gauss(0, 3.0)

p.heart_base_x = hx * diffusion + random.gauss(0, 0.2)
p.heart_base_y = hy * diffusion + random.gauss(0, 0.2)
p.heart_base_z = noise_z
p.text_base_x, p.text_base_y = text_points[i]

time_elapsed = 0
current_stage = 0 # 0:洛伦兹蝴蝶, 1:汇聚爱心, 2:呼吸爱心, 3:爱心收缩→爆炸→文字
color_index = 0
chaos_start_time = 0
is_in_chaos = False

# 阶段时间记录，保证心跳从0开始加速
stage1_start_time = 0 # 汇聚阶段开始时间
stage2_start_time = 0 # 呼吸爱心阶段开始时间
last_stage = 0 # 上一帧的阶段，用来检测阶段切换

current_angle_x, current_angle_y = 0, 0
prev_mouse_pos = Vector2(pygame.mouse.get_pos())

running = True
while running:
delta_time = clock.tick(60) / 1000
time_elapsed += delta_time
current_mouse_pos = Vector2(pygame.mouse.get_pos())
mouse_velocity = current_mouse_pos - prev_mouse_pos
prev_mouse_pos = current_mouse_pos

# 阶段切换时间记录
if current_stage!= last_stage:
if current_stage == 1:
stage1_start_time = time_elapsed
if current_stage == 2:
stage2_start_time = time_elapsed
last_stage = current_stage


for event in pygame.event.get():
if event.type == pygame.QUIT: running = False
if event.type == pygame.KEYDOWN:
# 重置键：回到初始红金+初始文字+洛伦兹开场
if event.key == pygame.K_1:
current_stage = 0
time_elapsed = 0
color_index = 0
current_text_index = 0
current_text = TEXT_LIST[current_text_index]
particles = [Particle() for _ in range(NUM_PARTICLES)]
text_points = get_text_points_autoscale(current_text, WIDTH, HEIGHT, NUM_PARTICLES)
for i, p in enumerate(particles):
p.text_base_x, p.text_base_y = text_points[i]

#
if event.key == pygame.K_TAB:
# 先判断：是否在
is_text_ready = (current_stage == 3) and (time_elapsed - chaos_start_time > T_CHAOS_DURATION)

if is_text_ready:
# 文字阶段：换颜色 + 换文字
color_index = (color_index + 1) % len(PALETTES)
current_text_index = (current_text_index + 1) % len(TEXT_LIST)
current_text = TEXT_LIST[current_text_index]
# 重新生成新文字的采样点，更新所有粒子的目标坐标
text_points = get_text_points_autoscale(current_text, WIDTH, HEIGHT, NUM_PARTICLES)
for i, p in enumerate(particles):
p.text_base_x, p.text_base_y = text_points[i]
else:
# 非文字阶段：只换颜色，不碰文字
color_index = (color_index + 1) % len(PALETTES)

# 流程控制键：空格
if event.key == pygame.K_SPACE:
# 洛伦兹阶段按空格：直接跳爱心汇聚
if current_stage == 0:
current_stage = 1
time_elapsed = LORENZ_AUTO_TRANSITION
# 爱心呼吸阶段按空格：触发爆炸→文字
elif current_stage == 2:
current_stage = 3
chaos_start_time = time_elapsed
is_in_chaos = True
# 文字成型阶段按空格：回到爱心阶段
elif current_stage == 3 and (time_elapsed - chaos_start_time > T_CHAOS_DURATION):
current_stage = 1
time_elapsed = LORENZ_AUTO_TRANSITION

# 拖尾背景
screen.blit(trail_surface, (0, 0))

# 鼠标视角追踪
current_angle_y += ((current_mouse_pos.x - CENTER_X) / CENTER_X * 0.7 - current_angle_y) * 0.1
current_angle_x += ((current_mouse_pos.y - CENTER_Y) / CENTER_Y * 0.7 - current_angle_x) * 0.1
is_mouse_moving = mouse_velocity.length_squared() > 1.0

# 幂函数淡入，开场更快更丝滑
fade_progress = min(math.pow(time_elapsed / FADE_IN_DURATION, 1.8), 1.0)

# 自动流程控制
if current_stage == 0 and time_elapsed > LORENZ_AUTO_TRANSITION:
current_stage = 1
if current_stage == 1 and time_elapsed > LORENZ_AUTO_TRANSITION + T_MORPH_DURATION:
current_stage = 2
if current_stage == 3 and time_elapsed - chaos_start_time > T_CHAOS_DURATION:
is_in_chaos = False

active_palette = PALETTES[color_index]

# 由慢到快的心跳计算
if current_stage == 2:
# 呼吸爱心阶段：主加速心跳
stage_time = time_elapsed - stage2_start_time
heart_rate = HEART_RATE_INIT + (HEART_RATE_MAX - HEART_RATE_INIT) * math.tanh(
stage_time * HEART_ACCEL_SPEED)
heart_amp = HEART_AMP_INIT + (HEART_AMP_MAX - HEART_AMP_INIT) * math.tanh(
stage_time * HEART_ACCEL_SPEED * 0.8)
elif current_stage == 1:
# 汇聚阶段：缓慢启动心跳，过渡到呼吸阶段
stage_time = time_elapsed - stage1_start_time
heart_rate = HEART_RATE_INIT * 0.8 + HEART_RATE_INIT * 0.2 * math.tanh(stage_time * 0.3)
heart_amp = HEART_AMP_INIT * 0.5
else:
# 其他阶段：默认基础值
heart_rate = HEART_RATE_INIT
heart_amp = HEART_AMP_INIT

# 粒子更新与渲染
for p in particles:
noise_x = math.sin(p.heart_base_y * 10 + time_elapsed * 5) * 1.0
noise_y = math.cos(p.heart_base_x * 10 + time_elapsed * 4) * 1.0

target_x, target_y = p.x, p.y
particle_alpha = 255 * fade_progress
gravity_pull = 0.08

# --- 状态机核心逻辑 ---
if current_stage == 0:
# 洛伦兹蝴蝶开场
dx = LORENZ_SIGMA * (p.lorenz_y - p.lorenz_x) * LORENZ_MOVE_SPEED
dy = (p.lorenz_x * (LORENZ_RHO - p.lorenz_z) - p.lorenz_y) * LORENZ_MOVE_SPEED
dz = (p.lorenz_x * p.lorenz_y - LORENZ_BETA * p.lorenz_z) * LORENZ_MOVE_SPEED

p.lorenz_x += dx
p.lorenz_y += dy
p.lorenz_z += dz

target_x = CENTER_X + p.lorenz_x * LORENZ_SCALE
target_y = CENTER_Y + p.lorenz_y * LORENZ_SCALE

current_gravity = 0.08 * fade_progress
p.vx += (target_x - p.x) * current_gravity
p.vy += (target_y - p.y) * current_gravity
p.vx *= (0.88 + 0.05 * fade_progress)
p.vy *= (0.88 + 0.05 * fade_progress)

elif current_stage == 1:
# 爱心汇聚阶段
t_morph = min((time_elapsed - LORENZ_AUTO_TRANSITION) / T_MORPH_DURATION, 1.0)
rx_h, ry_h, rz_h = rotate_3d(p.heart_base_x, p.heart_base_y, p.heart_base_z, current_angle_y,
current_angle_x)
heartbeat_curve = math.pow((math.sin(time_elapsed * heart_rate) + 1) / 2, 4)
scale = 14 + heartbeat_curve * heart_amp
target_x_h = CENTER_X + rx_h * scale + noise_x
target_y_h = CENTER_Y + ry_h * scale + noise_y

target_x = target_x_h
target_y = target_y_h
gravity_pull = 0.05 * t_morph
p.vx *= 0.88;
p.vy *= 0.88

elif current_stage == 2:
# 呼吸爱心阶段（由慢到快心跳）
rx, ry, rz = rotate_3d(p.heart_base_x, p.heart_base_y, p.heart_base_z, current_angle_y, current_angle_x)
heartbeat_curve = math.pow((math.sin(time_elapsed * heart_rate) + 1) / 2, 4)
scale = 14 + heartbeat_curve * heart_amp
target_x = CENTER_X + rx * scale + noise_x
target_y = CENTER_Y + ry * scale + noise_y
p.vx *= 0.82;
p.vy *= 0.82

elif current_stage == 3:
# 爱心收缩→爆炸→文字
time_in_stage = time_elapsed - chaos_start_time

if time_in_stage < 1.2:
# 爱心脉动收缩阶段
progress = time_in_stage / 1.2
final_heart_rate = HEART_RATE_MAX * 1.2
pulsate = math.sin(progress * math.pi * 4) * 1.5
scale = 14 * (1 - progress * 0.6) + pulsate + math.pow(
(math.sin(time_elapsed * final_heart_rate) + 1) / 2, 4) * 1.0

rx, ry, rz = rotate_3d(p.heart_base_x, p.heart_base_y, p.heart_base_z, current_angle_y,
current_angle_x)
target_x = CENTER_X + rx * scale + noise_x
target_y = CENTER_Y + ry * scale + noise_y
gravity_pull = 0.15
p.vx *= 0.85
p.vy *= 0.85

elif time_in_stage < 1.6:
# 超新星爆炸阶段
p.vx += random.uniform(-12, 12)
p.vy += random.uniform(-12, 12)
particle_alpha = int(255 * math.pow((1.0 - (time_in_stage - 1.2) / 0.4), 2))

else:
# 文字成型阶段
target_x = p.text_base_x + random.gauss(0, 0.3)
target_y = p.text_base_y + random.gauss(0, 0.3)
gravity_pull = 0.25
p.vx *= 0.78
p.vy *= 0.78

# --- 鼠标流体交互 ---
repulsion = Vector2(0, 0)
allow_interaction = (current_stage == 2) or (current_stage == 3 and (time_elapsed - chaos_start_time > 1.6))

if allow_interaction and is_mouse_moving:
dir_vec = Vector2(p.x, p.y) - current_mouse_pos
dist_sq = dir_vec.length_squared()
if 0 < dist_sq < 150 ** 2:
dist = math.sqrt(dist_sq)
force = (2000 / dist) * (mouse_velocity.length() * 0.05)
repulsion = dir_vec.normalize() * force

# 物理更新
p.vx += (target_x - p.x) * gravity_pull + repulsion.x * 0.1
p.vy += (target_y - p.y) * gravity_pull + repulsion.y * 0.1

# 速度限制
time_in_stage = time_elapsed - chaos_start_time if current_stage == 3 else 0
is_exploding = (current_stage == 3 and 1.2 <= time_in_stage < 1.6)
max_speed = 80 if is_exploding else 40
current_speed = math.hypot(p.vx, p.vy)
if current_speed > max_speed:
p.vx = (p.vx / current_speed) * max_speed
p.vy = (p.vy / current_speed) * max_speed

p.x += p.vx
p.y += p.vy

# --- 渲染 ---
if particle_alpha > 5:
base_color = active_palette[p.color_idx]
r, g, b = base_color

if current_stage == 0:
brightness = random.uniform(0.3, 0.6) * fade_progress
r = int(r * brightness);
g = int(g * brightness);
b = int(b * brightness)

pygame.draw.circle(screen, (r, g, b), (int(p.x), int(p.y)), int(p.size))

pygame.display.flip()

pygame.quit()
sys.exit()


if __name__ == "__main__":
main()
