import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Przebicie PN-EN 1992-1-1", layout="wide")

st.title("Kalkulator przebicia płyty płaskiej")
st.caption("Wersja prototypowa odtwarzająca tok obliczeń z artykułu M. Gołdyna, Inżynieria i Budownictwo 7/2020.")

st.warning(
    "Prototyp inżynierski do weryfikacji. Zakres V1: słup wewnętrzny prostokątny, "
    "obwód podstawowy w odległości 2d. Wyniki należy niezależnie sprawdzić przed użyciem projektowym."
)

with st.sidebar:
    st.header("Dane wejściowe")

    st.subheader("Geometria")
    h = st.number_input("Grubość płyty h [mm]", 100.0, 2000.0, 200.0, 5.0)
    d = st.number_input("Wysokość użyteczna d [mm]", 50.0, h, 158.0, 1.0)
    cx = st.number_input("Wymiar słupa cx [mm]", 100.0, 5000.0, 400.0, 10.0)
    cy = st.number_input("Wymiar słupa cy [mm]", 100.0, 5000.0, 400.0, 10.0)

    st.subheader("Oddziaływania")
    VEd = st.number_input("VEd [kN]", 0.0, 100000.0, 572.5, 1.0)
    MEd_y = st.number_input("MEd,y [kNm]", 0.0, 100000.0, 18.7, 0.1)
    MEd_z = st.number_input("MEd,z [kNm]", 0.0, 100000.0, 22.6, 0.1)

    st.subheader("Materiały")
    fck = st.number_input("fck [MPa]", 12.0, 120.0, 30.0, 1.0)
    fyk = st.number_input("fyk [MPa]", 200.0, 1000.0, 500.0, 10.0)
    gamma_c = st.number_input("γc [-]", 1.0, 2.0, 1.4, 0.05)

    st.subheader("Zbrojenie główne")
    phi_y = st.number_input("Øy [mm]", 4.0, 50.0, 16.0, 1.0)
    sy = st.number_input("Rozstaw sy [mm]", 40.0, 1000.0, 100.0, 5.0)
    phi_z = st.number_input("Øz [mm]", 4.0, 50.0, 16.0, 1.0)
    sz = st.number_input("Rozstaw sz [mm]", 40.0, 1000.0, 100.0, 5.0)
    dy = st.number_input("dy [mm]", 20.0, h, 150.0, 1.0)
    dz = st.number_input("dz [mm]", 20.0, h, 166.0, 1.0)

    st.subheader("Zbrojenie na przebicie")
    sr = st.number_input("sr – rozstaw obwodów [mm]", 20.0, 1000.0, 100.0, 5.0)

    st.markdown("**Pręty odgięte – wg przykładu Gołdyna**")
    alpha = st.number_input("α prętów odgiętych [°]", 1.0, 90.0, 30.0, 1.0)
    phi_bent = st.number_input("Ø pręta odgiętego [mm]", 4.0, 40.0, 12.0, 1.0)
    n_bent_dir = st.number_input("Liczba prętów w jednym kierunku [-]", 1, 100, 4, 1)
    sr_bent = st.number_input("sr – rozstaw promieniowy / obwodowy [mm]", 1.0, 2000.0, 237.0, 1.0)
    st_bent = st.number_input("st – rozstaw styczny elementów [mm]", 1.0, 5000.0, 344.0, 1.0)
    uout_eff_bent = st.number_input(
        "uout,ef z przyjętego rozmieszczenia [mm]",
        1.0, 100000.0, 4625.0, 1.0,
        help="Długość efektywnego zewnętrznego obwodu kontrolnego wyznaczona z geometrii rozmieszczenia prętów."
    )

# jednostki: mm, N, MPa
V_N = VEd * 1000.0

# Dla słupa wewnętrznego i obwodu w 2d:
u0 = 2.0 * (cx + cy)
u1 = 2.0 * (cx + cy) + 4.0 * math.pi * d

# Wymiary obwodu podstawowego użyte w uproszczonym beta z artykułu
by = cy + 4.0 * d
bz = cx + 4.0 * d

if VEd > 0:
    ey = MEd_y / VEd * 1000.0
    ez = MEd_z / VEd * 1000.0
else:
    ey = ez = 0.0

beta = 1.0 + 1.8 * math.sqrt((ey / bz) ** 2 + (ez / by) ** 2)

vEd_u1 = beta * V_N / (u1 * d)
vEd_u0 = beta * V_N / (u0 * d)

Asy = math.pi * phi_y**2 / 4.0
Asz = math.pi * phi_z**2 / 4.0
rho_y = Asy / (sy * dy)
rho_z = Asz / (sz * dz)
rho_l_raw = math.sqrt(rho_y * rho_z)
rho_l = min(rho_l_raw, 0.02)

k = min(1.0 + math.sqrt(200.0 / d), 2.0)
CRdc = 0.18 / gamma_c
vRdc_formula = CRdc * k * (100.0 * rho_l * fck) ** (1.0 / 3.0)
vmin = 0.035 * math.sqrt(k**3 * fck)
vRdc = max(vRdc_formula, vmin)

nu = 0.6 * (1.0 - fck / 250.0)
vRdmax_u0 = 0.4 * nu * fck / gamma_c
vRdmax_u1 = 1.5 * vRdc

uout_req = beta * V_N / (vRdc * d)

# Granica naprężenia w zbrojeniu na przebicie
fywd = fyk / 1.15
fywd_eff = min(250.0 + 0.25 * d, fywd)

# Strzemiona wg równania (2)
Asw_req_stirrups = max(
    0.0,
    (vEd_u1 - 0.75 * vRdc) * u1 * sr
    / (1.5 * fywd_eff)
)

# ---------------------------------------------------------
# PRĘTY ODGIĘTE – tok wg artykułu M. Gołdyna, I&B 7/2020
#
# Dla jednego obwodu prętów odgiętych autor, zgodnie z
# omawianą interpretacją PN-EN 1992-1-1, zastępuje d/sr
# mnożnikiem 0.67.
# ---------------------------------------------------------

bent_factor = 0.67
sin_alpha = math.sin(math.radians(alpha))
cos_alpha = math.cos(math.radians(alpha))

Asw_req_bent = max(
    0.0,
    (vEd_u1 - 0.75 * vRdc) * u1 * d
    / (1.5 * bent_factor * fywd_eff * sin_alpha)
)

area_bent = math.pi * phi_bent**2 / 4.0

# W przykładzie: 4Ø12 w każdym z dwóch ortogonalnych kierunków.
# Każdy pręt przecina rozpatrywany mechanizm w dwóch gałęziach:
# Asw,prov = 2 * (2 * n) * Aphi = 4*n*Aphi
Asw_prov_bent = 4.0 * n_bent_dir * area_bent

n_bent_dir_req = math.ceil(Asw_req_bent / (4.0 * area_bent))

# Minimalny przekrój pojedynczego elementu zbrojenia na przebicie
Asw_min_bent = (
    0.08
    / (1.5 * sin_alpha + cos_alpha)
    * math.sqrt(fck) / fyk
    * sr_bent * st_bent
)

min_area_ok_bent = area_bent >= Asw_min_bent
total_area_ok_bent = Asw_prov_bent >= Asw_req_bent

# Kontrole konstrukcyjne opisane w artykule
sr_radial_limit = 0.75 * d
sr_out_limit = 1.5 * d
sr_radial_ok = sr_bent <= sr_radial_limit

# Zewnętrzny obwód kontrolny
uout_eff_ok_bent = uout_eff_bent >= uout_req

# Efektywny przekrój zbrojenia w kierunku normalnym do rysy
Asw_eff_bent = Asw_prov_bent * sin_alpha

# Informacyjna nośność wg równania (2) z mnożnikiem 0.67
vRdcs_bent = (
    0.75 * vRdc
    + 1.5
    * bent_factor
    * Asw_prov_bent
    * fywd_eff
    * sin_alpha
    / (u1 * d)
)
vRd_bent = min(vRdcs_bent, vRdmax_u1)
bent_ratio = 100.0 * vEd_u1 / vRd_bent if vRd_bent > 0 else math.inf

bent_all_ok = (
    total_area_ok_bent
    and min_area_ok_bent
    and sr_radial_ok
    and uout_eff_ok_bent
    and vEd_u1 <= vRd_bent
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("β", f"{beta:.3f}")
c2.metric("u₁", f"{u1/1000:.3f} m")
c3.metric("vEd(u₁)", f"{vEd_u1:.3f} MPa")
c4.metric("vRd,c", f"{vRdc:.3f} MPa")

st.divider()

left, right = st.columns([1.15, 0.85])

with left:
    st.header("Tok obliczeń")

    st.subheader("1. Mimośrody i współczynnik β")
    st.latex(r"e_y=M_{Ed,y}/V_{Ed},\qquad e_z=M_{Ed,z}/V_{Ed}")
    st.write(f"ey = **{ey:.1f} mm**, ez = **{ez:.1f} mm**")
    st.latex(r"\beta=1+1.8\sqrt{(e_y/b_z)^2+(e_z/b_y)^2}")
    st.write(f"β = **{beta:.3f}**")

    st.subheader("2. Obwód podstawowy i naprężenie styczne")
    st.write(f"u₀ = **{u0/1000:.3f} m**")
    st.write(f"u₁ = **{u1/1000:.3f} m**")
    st.latex(r"v_{Ed}=\beta\frac{V_{Ed}}{u_1d}")
    st.write(f"vEd(u₁) = **{vEd_u1:.3f} MPa**")

    st.subheader("3. Nośność betonu bez zbrojenia na przebicie")
    st.write(f"ρy = {rho_y:.5f}, ρz = {rho_z:.5f}")
    st.write(f"ρl = √(ρy·ρz) = **{rho_l_raw:.5f}**; do obliczeń: **{rho_l:.5f}**")
    st.write(f"k = **{k:.3f}**, CRd,c = **{CRdc:.3f}**")
    st.write(f"vRd,c ze wzoru = **{vRdc_formula:.3f} MPa**")
    st.write(f"vmin = **{vmin:.3f} MPa**")
    st.write(f"Przyjęto vRd,c = **{vRdc:.3f} MPa**")

    ratio = 100.0 * vEd_u1 / vRdc
    if vEd_u1 <= vRdc:
        st.success(f"PRZEBICIE BEZ ZBROJENIA SPEŁNIONE — wykorzystanie {ratio:.1f}%")
    else:
        st.error(f"PRZEBICIE BEZ ZBROJENIA NIESPEŁNIONE — wykorzystanie {ratio:.1f}%")

    st.subheader("4. Kontrola maksymalnych naprężeń")
    st.write(f"vEd(u₀) = **{vEd_u0:.3f} MPa**")
    st.write(f"vRd,max(u₀) = **{vRdmax_u0:.3f} MPa**")
    st.write(f"1.5·vRd,c = **{vRdmax_u1:.3f} MPa**")

    if vEd_u0 <= vRdmax_u0 and vEd_u1 <= vRdmax_u1:
        st.success("Warunki maksymalnych naprężeń spełnione.")
    else:
        st.error("Przekroczono co najmniej jeden warunek maksymalnych naprężeń.")

    if vEd_u1 > vRdc:
        st.subheader("5. Wymagane zbrojenie na przebicie")
        tab1, tab2 = st.tabs(["Strzemiona", "Pręty odgięte"])

        with tab1:
            st.latex(
                r"A_{sw}=\frac{(v_{Ed}-0.75v_{Rd,c})u_1s_r}"
                r"{1.5f_{ywd,ef}\sin\alpha}"
            )
            st.write(f"fywd,ef = **{fywd_eff:.1f} MPa**")
            st.write(f"Wymagane Asw = **{Asw_req_stirrups:.0f} mm² / obwód**")
            area6 = math.pi * 6**2 / 4
            n6 = math.ceil(Asw_req_stirrups / area6)
            st.info(f"Orientacyjnie: {n6} gałęzi Ø6 → {n6*area6:.0f} mm²/obwód")

        with tab2:
            st.markdown("### Pręty odgięte – sprawdzenie wg przykładu z artykułu")

            st.info(
                "Dla jednego obwodu prętów odgiętych przyjęto mnożnik **0,67** "
                "zamiast ilorazu d/sr – zgodnie z tokiem przykładu Gołdyna."
            )

            st.latex(
                r"A_{sw,req}="
                r"\frac{(v_{Ed}-0.75v_{Rd,c})u_1d}"
                r"{1.5\cdot0.67\cdot f_{ywd,ef}\sin\alpha}"
            )

            st.write(f"α = **{alpha:.0f}°**, sin α = **{sin_alpha:.3f}**")
            st.write(f"fywd,ef = **{fywd_eff:.1f} MPa**")
            st.metric("Wymagane Asw,req", f"{Asw_req_bent:.0f} mm²")

            st.markdown("#### 1. Dobór liczby prętów")

            st.latex(
                r"A_{sw,prov}=2(2n)A_{\phi}=4nA_{\phi}"
            )

            st.write(
                f"Przyjęto **{n_bent_dir}Ø{phi_bent:.0f} w każdym z dwóch "
                f"ortogonalnych kierunków**."
            )
            st.write(f"AØ = **{area_bent:.1f} mm²**")
            st.write(
                f"Asw,prov = 4 × {n_bent_dir} × {area_bent:.1f} "
                f"= **{Asw_prov_bent:.0f} mm²**"
            )
            st.write(
                f"Wymagana minimalna liczba: **{n_bent_dir_req} prętów "
                f"w każdym kierunku**."
            )

            if total_area_ok_bent:
                st.success(
                    f"Asw,prov = {Asw_prov_bent:.0f} mm² ≥ "
                    f"Asw,req = {Asw_req_bent:.0f} mm² — SPEŁNIONE"
                )
            else:
                st.error(
                    f"Asw,prov = {Asw_prov_bent:.0f} mm² < "
                    f"Asw,req = {Asw_req_bent:.0f} mm² — NIESPEŁNIONE"
                )

            st.markdown("#### 2. Minimalny przekrój pojedynczego elementu")

            st.latex(
                r"A_{sw,min}="
                r"\frac{0.08}{1.5\sin\alpha+\cos\alpha}"
                r"\frac{\sqrt{f_{ck}}}{f_{yk}}s_rs_t"
            )

            st.write(f"sr = **{sr_bent:.0f} mm**")
            st.write(f"st = **{st_bent:.0f} mm**")
            st.write(f"Asw,min = **{Asw_min_bent:.2f} mm²**")
            st.write(f"AØ{phi_bent:.0f} = **{area_bent:.2f} mm²**")

            if min_area_ok_bent:
                st.success(
                    f"AØ = {area_bent:.2f} mm² ≥ "
                    f"Asw,min = {Asw_min_bent:.2f} mm² — SPEŁNIONE"
                )
            else:
                st.error(
                    f"AØ = {area_bent:.2f} mm² < "
                    f"Asw,min = {Asw_min_bent:.2f} mm² — NIESPEŁNIONE"
                )

            st.markdown("#### 3. Kontrola rozstawu promieniowego")

            st.latex(r"s_r\leq0.75d")

            st.write(
                f"sr = **{sr_bent:.0f} mm**, "
                f"0.75d = **{sr_radial_limit:.1f} mm**"
            )

            if sr_radial_ok:
                st.success("Warunek sr ≤ 0.75d — SPEŁNIONY")
            else:
                st.error("Warunek sr ≤ 0.75d — NIESPEŁNIONY")

            st.caption(
                f"Dodatkowo w przykładzie kontrolowana jest odległość od uout "
                f"do ostatniego obwodu: sr,out ≤ 1.5d = {sr_out_limit:.1f} mm. "
                "Jej pełna automatyzacja wymaga jawnego modelu geometrii odgięcia."
            )

            st.markdown("#### 4. Zewnętrzny obwód kontrolny")

            st.write(f"uout,req = **{uout_req:.0f} mm**")
            st.write(f"uout,ef = **{uout_eff_bent:.0f} mm**")

            if uout_eff_ok_bent:
                st.success("uout,ef ≥ uout,req — SPEŁNIONE")
            else:
                st.error(
                    "uout,ef < uout,req — zasięg przyjętego zbrojenia "
                    "jest niewystarczający."
                )

            st.markdown("#### 5. Kontrola nośności z przyjętego Asw")

            st.write(f"Asw,ef = Asw,prov·sin α = **{Asw_eff_bent:.0f} mm²**")
            st.write(f"vRd,cs = **{vRdcs_bent:.3f} MPa**")
            st.write(f"limit 1.5·vRd,c = **{vRdmax_u1:.3f} MPa**")
            st.write(f"vRd przyjęte do kontroli = **{vRd_bent:.3f} MPa**")
            st.write(f"vEd = **{vEd_u1:.3f} MPa**")

            if vEd_u1 <= vRd_bent:
                st.success(
                    f"vEd ≤ vRd — wykorzystanie {bent_ratio:.1f}%"
                )
            else:
                st.error(
                    f"vEd > vRd — wykorzystanie {bent_ratio:.1f}%"
                )

            st.markdown("#### Wynik końcowy – pręty odgięte")

            if bent_all_ok:
                st.success(
                    "PRĘTY ODGIĘTE: WARUNKI OBLICZENIOWE WPROWADZONE "
                    "W APLIKACJI SĄ SPEŁNIONE."
                )
            else:
                st.error(
                    "PRĘTY ODGIĘTE: CO NAJMNIEJ JEDEN WARUNEK JEST NIESPEŁNIONY."
                )

            st.warning(
                "Kontrole położenia końca odgięcia ≤ 0.25d, górnego odgięcia "
                "≤ 0.5d oraz dolnego odgięcia około 2d nie są jeszcze liczone "
                "automatycznie. Wymagają modułu geometrii pręta."
            )

    st.subheader("6. Zewnętrzny obwód kontrolny")
    st.latex(r"u_{out,req}=\beta\frac{V_{Ed}}{v_{Rd,c}d}")
    st.write(f"uout,req = **{uout_req/1000:.3f} m**")

with right:
    st.header("Schemat")

    fig, ax = plt.subplots(figsize=(7, 7))

    ax.add_patch(Rectangle((-cx/2, -cy/2), cx, cy, fill=False, linewidth=2))
    ax.text(0, 0, "SŁUP", ha="center", va="center")

    def rounded_rect_points(offset, n_arc=40):
        r = offset
        pts = []
        centers = [
            (cx/2, cy/2, 0, 90),
            (-cx/2, cy/2, 90, 180),
            (-cx/2, -cy/2, 180, 270),
            (cx/2, -cy/2, 270, 360),
        ]
        for xc, yc, a0, a1 in centers:
            for a in [a0 + (a1-a0)*i/(n_arc-1) for i in range(n_arc)]:
                ar = math.radians(a)
                pts.append((xc+r*math.cos(ar), yc+r*math.sin(ar)))
        pts.append(pts[0])
        return pts

    p1 = rounded_rect_points(2*d)
    ax.plot([p[0] for p in p1], [p[1] for p in p1], label="u₁ = 2d")

    scale = max(1.0, uout_req/u1)
    pout = [(x*scale, y*scale) for x, y in p1]
    ax.plot(
        [p[0] for p in pout],
        [p[1] for p in pout],
        linestyle="--",
        label="u_out,req – orientacyjnie"
    )

    lim = max(
        max(abs(x) for x, y in pout),
        max(abs(y) for x, y in pout),
        cx,
        cy
    ) * 1.2

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.grid(True, alpha=0.25)
    ax.legend()
    st.pyplot(fig)

    st.caption(
        "Uwaga: u_out na schemacie V1 jest wizualizacją orientacyjną. "
        "Algorytm dokładnego rozmieszczenia obwodów zbrojenia będzie kolejnym etapem."
    )

st.divider()
st.subheader("Test referencyjny z artykułu")
st.write(
    "Dla wartości domyślnych aplikacja powinna odtworzyć w przybliżeniu: "
    "**β = 1.092, u₁ = 3.585 m, vEd = 1.104 MPa, vRd,c = 0.852 MPa, "
    "Asw strzemion ≈ 384 mm²/obwód oraz uout,req ≈ 4.64 m**."
)

checks = {
    "β": abs(beta - 1.092) < 0.005,
    "u₁": abs(u1/1000 - 3.585) < 0.005,
    "vEd": abs(vEd_u1 - 1.104) < 0.005,
    "vRd,c": abs(vRdc - 0.852) < 0.005,
    "Asw": abs(Asw_req_stirrups - 384) < 5,
}

if all(checks.values()):
    st.success("TEST REFERENCYJNY: PASS")
else:
    st.warning("TEST REFERENCYJNY: część wartości odbiega od przykładu.")
    st.write(checks)
