# -*- coding: utf_8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import rcParams
import io
import os

# 日本語フォントを設定（Windowsなら Meiryo、Macなら Hiragino、Linuxなら IPAexGothic が一般的）
rcParams['font.family'] = 'Meiryo'  # ← Windows用。なければ 'MS Gothic' でもOK

st.title("RTU結果から作業時間を分析するアプリ")

folder_path = st.text_input("CSVのあるフォルダのフルパスを入力してください:")

if folder_path and os.path.isdir(folder_path):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    selected_csv = st.selectbox("CSVファイルを選んでください", csv_files)

    if selected_csv:
        csv_path = os.path.join(folder_path, selected_csv)
        df = pd.read_csv(csv_path, encoding="cp932", on_bad_lines="skip")

        if set(["日時", "ファイル名", "判定結果"]).issubset(df.columns):
            df = df[["日時", "ファイル名", "判定結果"]]
            df["日時"] = pd.to_datetime(df["日時"], errors="ignore")
            df = df.sort_values("日時").reset_index(drop=True)
            df.insert(df.columns.get_loc("ファイル名")+1, "Time", df["日時"].diff().dt.total_seconds())

            #st.dataframe(df)

            st.write("### テーブル（行頭をクリックして画像を表示）")

            # 行選択イベントの有効化
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",   # 単一行選択
                on_select="rerun",             # 選択時に再実行
                key="df_table"
            )

            # 選択された行のインデックスを取得
            if event and event.selection.rows:
                row_index = event.selection.rows[0]
                selected_file = df.iloc[row_index]["ファイル名"]

                # CSVと同じフォルダのresultを探す（ここでは仮にカレントディレクトリと同じ扱い）
                base_dir = os.getcwd()
                result_dir = os.path.join(folder_path, "Result")
                img_path = os.path.join(result_dir, selected_file)

                if os.path.exists(img_path):
                    st.image(img_path, caption=selected_file, use_container_width=True)
                else:
                    st.error(f"画像が見つかりません: {img_path}")



    # セッションに保存
    st.session_state["df"] = df

# -------------------------
# セッションからdfを利用
# -------------------------
if "df" in st.session_state:
    df = st.session_state["df"]

    #st.write("処理後のデータ（日時順、Time列は秒単位）")
    #st.dataframe(df)

    def plot_graph():
        column = "Time"
        # bins 数を調整できるスライダー
        bins = st.slider("ビンの数 (棒の数)", min_value=5, max_value=100, value=50)

        # データ範囲の下限・上限をスライダーで指定（レンジ指定）
        min_val = int(df[column].min())
        max_val = int(df[column].max())
        range_values = st.slider(
            "表示する数値の範囲",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),  # 初期は全範囲
            step=1
        )
        lower, upper = range_values

        # 下限～上限でフィルタリング
        filtered_data = df[(df[column] >= lower) & (df[column] <= upper)][column]

        # ヒストグラム描画
        fig, ax = plt.subplots()
        ax.hist(filtered_data, bins=bins, color="skyblue", edgecolor="black")
        ax.set_title(f"{column} hist")
        ax.set_xlabel(column + " (sec)")
        ax.set_ylabel("count")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        # ▼ 平均値・中央値を表示するボタン
        if st.button("平均値と中央値を計算"):
            mean_val = filtered_data.mean()
            median_val = filtered_data.median()

            # グラフに埋め込み
            text_str = f"平均値: {mean_val:.2f} sec\n中央値: {median_val:.2f} sec"
            ax.text(
                0.95, 0.95, text_str,
                transform=ax.transAxes,  # 軸に対する相対座標 (0~1)
                fontsize=10,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="gray")  # 背景枠
            )

            # PNG バッファに保存
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)

            # ダウンロードボタン
            st.download_button(
                label="グラフをダウンロード",
                data=buf,
                file_name="histogram_with_stats.png",
                mime="image/png"
            )

        st.pyplot(fig)

    # グラフを表示するボタン
    if st.button("ヒストグラムを表示"):
        st.session_state["show_graph"] = True

    # フラグがある場合はグラフを表示
    if st.session_state.get("show_graph", False):
        plot_graph()
else:
    st.warning("CSVファイルをアップロードしてください。")