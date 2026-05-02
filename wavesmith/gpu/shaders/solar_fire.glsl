#version 330

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform float u_time;
uniform float u_progress;
uniform float u_rms;
uniform float u_bass;
uniform float u_mid;
uniform float u_treble;
uniform float u_beat;
uniform float u_beat_decay;
uniform float u_slow_pulse;
uniform vec3 u_palette_base;
uniform vec3 u_palette_accent;
uniform vec3 u_palette_beat;
uniform float u_spectrum[32];
uniform float u_detail;
uniform float u_bloom_strength;
uniform float u_warp_strength;
uniform float u_line_strength;
uniform float u_exposure;
uniform float u_softness;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(113.5, 271.9))) * 41538.173);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
    float value = 0.0;
    float amp = 0.54;
    for (int i = 0; i < 5; i++) {
        value += noise(p) * amp;
        p = mat2(1.58, -1.04, 1.04, 1.58) * p + vec2(6.1, 2.7);
        amp *= 0.52;
    }
    return value;
}

float spectrumAt(float amount) {
    float index = fract(amount) * 32.0;
    int left = int(floor(index)) % 32;
    int right = (left + 1) % 32;
    return mix(u_spectrum[left], u_spectrum[right], fract(index));
}

float loopArc(vec2 p, vec2 foot_a, vec2 foot_b, vec2 lift, float width, float phase) {
    float best = 0.0;
    for (int i = 0; i < 32; i++) {
        float t0 = float(i) / 32.0;
        float t1 = float(i + 1) / 32.0;
        vec2 a = mix(foot_a, foot_b, t0) + lift * sin(t0 * 3.14159265);
        vec2 b = mix(foot_a, foot_b, t1) + lift * sin(t1 * 3.14159265);
        a += vec2(sin(t0 * 7.0 + phase), cos(t0 * 5.0 - phase * 0.45)) * width * 0.62;
        b += vec2(sin(t1 * 7.0 + phase), cos(t1 * 5.0 - phase * 0.45)) * width * 0.62;
        vec2 pa = p - a;
        vec2 ba = b - a;
        float h = clamp(dot(pa, ba) / max(0.0001, dot(ba, ba)), 0.0, 1.0);
        float d = length(pa - ba * h);
        float t = mix(t0, t1, h);
        float strand = exp(-pow(d / max(0.022, width * 1.05), 1.35) * 2.0);
        float core = exp(-pow(d / max(0.018, width * 0.36), 1.22) * 2.6);
        float halo = exp(-pow(d / max(0.04, width * 3.8), 1.45) * 1.7);
        float taper = smoothstep(0.0, 0.16, t) * (1.0 - smoothstep(0.84, 1.0, t));
        best = max(best, (halo * 0.055 + strand * 0.42 + core * 0.13) * taper);
    }
    return best;
}

float magneticVeil(vec2 p, vec2 foot_a, vec2 foot_b, vec2 lift, float width, float phase) {
    float veil = 0.0;
    for (int i = 0; i < 9; i++) {
        float lane = (float(i) - 4.0) / 4.0;
        float wobble = sin(phase * 0.47 + lane * 2.7);
        vec2 offset_a = normalize(foot_b - foot_a) * lane * width * (2.2 + wobble * 0.35);
        vec2 offset_b = normalize(foot_b - foot_a) * lane * width * (3.6 - wobble * 0.3);
        vec2 strand_lift = lift * (0.8 + 0.18 * lane + 0.08 * wobble);
        strand_lift += vec2(-lift.y, lift.x) * lane * 0.045;
        float strand = loopArc(
            p,
            foot_a + offset_a,
            foot_b + offset_b,
            strand_lift,
            width * (1.15 + 0.18 * abs(lane)),
            phase + lane * 3.1
        );
        veil += strand * (0.16 + 0.08 * (1.0 - abs(lane)));
    }
    return veil;
}

float eruptionCloud(vec2 p, vec2 base, vec2 normal, vec2 tangent, float height, float width, float phase) {
    vec2 q = p - base;
    float up = dot(q, normal);
    float side = dot(q, tangent);
    float rise = clamp(up / max(0.02, height), 0.0, 1.4);
    float curl = sin(rise * 5.4 + phase) * width * (0.42 + rise * 1.1);
    curl += sin(rise * 11.0 - phase * 0.48) * width * 0.34;
    float radius = width * (2.0 + rise * 3.2);
    float side_field = exp(-pow(abs(side - curl) / max(0.02, radius), 1.38));
    float fan_field = exp(-pow(abs(side + curl * 0.45) / max(0.02, radius * (1.8 + rise)), 1.22));
    float vertical = smoothstep(-0.04, height * 0.12, up)
        * (1.0 - smoothstep(height * 0.24, height * 1.42, up));
    float turbulent = fbm(p * 8.4 + vec2(phase * 0.08, -phase * 0.13));
    float inner_flow = fbm(vec2(side * 10.0, rise * 6.0 - phase * 0.15));
    float broken = smoothstep(0.2, 0.94, turbulent * 0.62 + inner_flow * 0.55);
    return (side_field * 0.66 + fan_field * 0.34) * vertical * (0.34 + broken * 0.56);
}

float sourceGlow(vec2 p, vec2 source, vec2 normal, vec2 tangent, float width, float phase) {
    vec2 q = p - source;
    float up = max(0.0, dot(q, normal));
    float side = abs(dot(q, tangent));
    float oval = exp(-side * (10.0 / max(0.04, width))) * exp(-up * (5.2 / max(0.08, width)));
    float rays = 0.0;
    for (int i = 0; i < 5; i++) {
        float lane = (float(i) - 2.0) * 0.4;
        float d = abs(side - width * lane * 1.9 - sin(up * 9.0 + phase + lane) * width);
        rays += exp(-d * (5.0 / max(0.04, width))) * exp(-up * (3.6 / max(0.1, width)));
    }
    return oval * 0.48 + rays * 0.08;
}

void main() {
    vec2 aspect = vec2(u_resolution.x / max(1.0, u_resolution.y), 1.0);
    vec2 p = (v_uv - 0.5) * aspect;
    float detail = clamp(u_detail, 0.05, 1.5);
    float softness = clamp(u_softness, 0.0, 1.5);
    float pulse = max(u_bass, u_slow_pulse * 0.92) + u_beat_decay * 0.25 + u_beat * 0.2;

    vec2 sun_center = vec2(0.0, -1.06);
    float sun_radius = 0.96 + u_bass * 0.035;
    vec2 solar = p - sun_center;
    float radius = length(solar);
    float angle = atan(solar.y, solar.x);
    float surface_distance = abs(radius - sun_radius);
    float disk = 1.0 - smoothstep(sun_radius - 0.035, sun_radius + 0.015, radius);
    float rim = exp(-surface_distance * (24.0 + detail * 28.0));
    float corona = exp(-max(0.0, radius - sun_radius) * (8.2 - u_bass * 0.9));

    vec2 flow = vec2(angle * 1.8, radius * 5.8 - u_time * (0.18 + u_mid * 0.16));
    float granules = fbm(flow * (2.0 + detail * 1.6));
    float cells = fbm(flow * (6.0 + detail * 4.5) + vec2(u_time * 0.05, -u_time * 0.08));
    float surface = disk * (0.38 + granules * 0.34 + cells * 0.26);

    float prominences = 0.0;
    float veils = 0.0;
    float wisps = 0.0;
    float eruptions = 0.0;
    float source_bursts = 0.0;
    float sparks = 0.0;
    for (int i = 0; i < 11; i++) {
        float fi = float(i);
        float t = fi / 10.0;
        float center_angle = mix(0.32, 0.68, t) * 3.14159265 + sin(fi * 5.17) * 0.035;
        float spread = 0.07 + 0.035 * sin(fi * 2.4);
        float amount = spectrumAt(t * 0.86 + 0.07);
        float life = 0.5 + 0.5 * sin(u_time * (0.11 + 0.022 * fi) + fi * 1.71);
        float growth = smoothstep(0.12, 0.86, life);
        float fall = 1.0 - smoothstep(0.64, 1.0, life);
        float fade_out = mix(0.42, 1.0, fall);
        float gate = smoothstep(0.28, 0.78, life + amount * 0.34 + u_bass * 0.16);
        float active_level = gate * gate * fade_out;
        vec2 normal = vec2(cos(center_angle), sin(center_angle));
        vec2 tangent = vec2(-normal.y, normal.x);
        vec2 foot_a = sun_center + vec2(cos(center_angle - spread), sin(center_angle - spread)) * sun_radius;
        vec2 foot_b = sun_center + vec2(cos(center_angle + spread), sin(center_angle + spread)) * sun_radius;
        float height = 0.2 + amount * 0.24 + u_slow_pulse * 0.12 + growth * 0.34;
        vec2 lift = normal * height + tangent * sin(u_time * 0.14 + fi) * height * 0.24;
        float width = 0.045 + amount * 0.028 + u_line_strength * 0.012;
        float flare = loopArc(p, foot_a, foot_b, lift, width, u_time * 0.55 + fi * 2.3);
        prominences += flare * active_level * 0.58;
        veils += magneticVeil(p, foot_a, foot_b, lift, width * 1.08, u_time * 0.36 + fi * 2.3)
            * active_level
            * (0.58 + amount * 0.32 + u_mid * 0.2);

        vec2 source = mix(foot_a, foot_b, 0.5);
        source_bursts += sourceGlow(p, source, normal, tangent, width * 2.7, u_time * 0.42 + fi)
            * active_level
            * (0.58 + u_bass * 0.92 + u_beat_decay * 0.5);
        float eruption_height = height * (0.78 + pulse * 0.36 + growth * 0.32);
        float eruption_width = width * (1.08 + u_bass * 0.62 + growth * 0.68);
        eruptions += eruptionCloud(
            p,
            source,
            normal,
            tangent,
            eruption_height,
            eruption_width,
            u_time * (0.62 + amount * 0.2) + fi * 2.9
        ) * active_level * (0.48 + u_bass * 0.54 + u_beat_decay * 0.34);

        for (int j = 0; j < 5; j++) {
            float fj = float(j);
            float side = fj - 2.0;
            float split = smoothstep(0.2, 0.86, growth + amount * 0.2);
            float branch_phase = u_time * (0.34 + fj * 0.07) + fi * 1.4 + fj * 2.1;
            vec2 branch_a = foot_a + tangent * side * width * (0.45 + split * 0.45) + normal * width * 0.35;
            vec2 branch_b = foot_b + tangent * side * width * (0.65 + split * 0.85) + normal * width * 0.35;
            vec2 branch_lift = lift * (1.04 + split * (0.08 + fj * 0.025));
            branch_lift += tangent * side * width * (2.8 + split * 4.6);
            float branch_width = width * (0.62 - fj * 0.055);
            float branch = loopArc(p, branch_a, branch_b, branch_lift, branch_width, branch_phase);
            float treble_flicker = 0.72 + u_treble * 0.55 + sin(branch_phase * 1.7) * 0.12;
            float outer_fade = mix(1.0, 0.5, abs(side) / 2.0);
            wisps += branch * active_level * split * treble_flicker * outer_fade * (0.07 + amount * 0.12);
        }

        vec2 spark_pos = mix(foot_a, foot_b, 0.5) + lift * (0.9 + life * 0.18);
        sparks += exp(-length(p - spark_pos) * (14.0 + detail * 14.0)) * amount * active_level;
    }

    float heat_haze = fbm(p * (5.5 + detail * 2.5) + vec2(u_time * 0.08, -u_time * 0.18));
    float plasma_noise = fbm(p * (12.0 + detail * 6.0) + vec2(u_time * 0.12, -u_time * 0.24));
    prominences *= 0.78 + plasma_noise * 0.32;
    veils *= 0.04 + plasma_noise * 0.04;
    wisps *= 0.62 + plasma_noise * 0.44;
    eruptions *= 0.055 + plasma_noise * 0.055;
    float smoke = smoothstep(0.9, 0.998, heat_haze) * corona * 0.002;
    float bloom = surface * 0.24 + rim * (0.3 + pulse * 0.38);
    bloom += corona * 0.012 + source_bursts * 1.48 + eruptions * 0.38 + veils * 0.18 + prominences * 1.42 + wisps * 0.72 + sparks * 0.28 + smoke * 0.04;
    bloom *= u_bloom_strength;

    vec3 deep = vec3(0.012, 0.002, 0.0);
    vec3 ember = mix(u_palette_base, u_palette_accent, 0.36);
    vec3 color = mix(deep, ember, clamp(surface + smoke * 0.2, 0.0, 1.0));
    color = mix(color, u_palette_accent, clamp(rim * 0.5 + source_bursts * 0.82 + eruptions * 0.6 + veils * 0.5 + prominences * 0.36 + wisps * 0.2, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(source_bursts * 0.78 + sparks * 0.15 + pulse * rim * 0.22 + eruptions * 0.18, 0.0, 1.0));
    color += u_palette_base * eruptions * 0.42;
    color += u_palette_base * veils * 0.26;
    color += u_palette_accent * bloom * 0.22;
    color += u_palette_beat * pow(max(0.0, bloom), 1.45 + detail * 0.18) * 0.14;

    float vignette = 1.0 - smoothstep(0.16, 1.22, length(p));
    color *= vignette;
    color = vec3(1.0) - exp(-color * (u_exposure + pulse * 0.48));
    color = pow(color, vec3(0.88 + softness * 0.08));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
