# 個人事業主向け勤怠管理システム

個人事業主を始めるにあたり、参画先、仲介、保育園提出様式などフォーマットが異なる入力に対して管理しやすいように、自分向けのシステムを作っています。  
開始時間、終了時間、休憩（分）、中断開始、中断終了、その他（副業など）を入力することで、参画先と仲介の異なる入力にも機械的に入力できるよう対応しています。  
具体的には、開始、終了、休憩を入力するケースと、開始、終了、中断時間を入力するケース、月々の休憩含む総時間を記入するケースです。  
  
そのうち仲介会社へのWeb入力はSeleniumで自動にしたいですね。

## 機能概略

- __勤怠入力機能（input画面）__
  - 開始時刻、終了時刻、休憩時間の入力
  - 開始時刻、終了時刻、休憩時間を入力せず、副業のみを入力するケースにも対応（休日など）
  - 中断の開始と終了の入力。複数回入力できる。
    - ToDo：今の所時間の重複チェックがない。
  - 副業時間の入力。
  - 登録時に、仲介会社への入力に必要な、開始、終了、休憩合計の計算結果を表示。
  - 入力したかどうかカレンダー表示する機能。
  - 内容などのコメント入力。
- __勤怠集計、編集機能（edit画面）__
  - 入力済みデータの編集。
  - 入力済みデータの削除。
  - 1ヶ月の集計
    - 勤務日数：開始、終了に入力がある日のカウント
    - 総勤務時間：休憩、副業含めた全ての時間。保育園提出用。
    - 勤務合計：開始と終了からのみ算出したもの。拘束時間に該当。副業は含まない。
    - 実働時間：勤務合計から休憩と中断を除いた時間。請求工数に該当。
    - 休憩合計：休憩時間の合計
    - 中断合計：中断時間の合計
    - 副業合計：副業時間の合計
  - 入力したかどうかリンク付きでカレンダー表示する機能。クリックでその日の編集に飛べる。
- __ToDo: ダッシュボード（dashboard画面）__
  - 月別の勤務時間内訳積み重ねの推移を表示
  - 日毎の勤務時間の累積を表示
  - 1ヶ月の集計表示
  - 1年の集計表示

## 使用方法

Dockerがインストールされていれば使えます。Pythonや必要なモジュールが自動ダウンロードされますので、インターネット環境が必要です。

- コードをローカルへ保存。フォークとかよくわからんという人はZIPダウンロードで。
- 保存したフォルダへ移動。
  - VSCodeの場合
    - ファイル → 開く → work-manager(または変更したフォルダ名)
    - ターミナル → 新しいターミナル → 下のdockerコマンド
- Docker composeを使用し起動。

```bash
    docker compose up --build
```

- [http://localhost:8501](http://localhost:8501)で入力ページにアクセス
- ルータで対象PCのIPを固定にすれば、自宅内のWiFi環境であればIP:8501でスマホなどからもアクセス可能。

## フォルダ構造

フロントエンド（Streamlit）とバックエンド（FastAPI）でフォルダとDockerを分けています。  
Docker composeで立ち上げれば、両方勝手に立ち上がります。手動で立ち上げる場合はfrontとbackそれぞれDockerで立ち上げてください。
ui_components.pyが特にとっちらかっているので、いつか整理します・・・

```txt
work-manager/
├── back/                        # バックエンド（FastAPI）
│   ├── database.py              # DB接続・セッション管理・Baseクラス定義
│   ├── main.py                  # FastAPIアプリのエントリーポイント
│   ├── models.py                # 勤怠データなどのORMモデル（テーブル定義）
│   ├── schemas.py               # API入出力用のPydanticスキーマ（バリデーション・型定義）
│   ├── requirements.txt         # バックエンドの依存パッケージ
│   ├── Dockerfile               # バックエンド用Dockerfile
│   ├── attendance.db            # SQLiteデータベース（永続化用）
│   └── routers/                 # APIルータ（機能別分割）
│       ├── attendance.py            # 勤怠データのCRUD API
│       └── attendance_summary.py    # 勤怠集計API
├── front/                       # フロントエンド（Streamlit）
│   ├── input.py                 # 勤怠入力ページ（メイン画面）
│   ├── settings.py              # API URLやデフォルト値などの設定
│   ├── requirements.txt         # フロントエンドの依存パッケージ
│   ├── Dockerfile               # フロントエンド用Dockerfile
│   ├── modules/                 # 共通ロジック・UI部品
│   │   ├── api_client.py            # API通信処理
│   │   ├── attendance_utils.py      # 勤怠集計・ロジック
│   │   ├── session.py               # セッション管理
│   │   ├── time_utils.py            # 日付・時刻変換ユーティリティ
│   │   └── ui_components.py         # Streamlit用UI部品
│   └── pages/                   # Streamlitマルチページ
│       ├── dashboard.py             # ダッシュボード画面
│       └── edit.py                  # 編集・集計画面
├── docker-compose.yml            # バックエンド・フロントエンドのサービスを一括起動するDocker構成ファイル
├── README.md                     # プロジェクトの概要・利用方法
└── LICENSE                       # ライセンス情報
```

## ORMモデル仕様

DB管理しているのは今の所この1テーブルのみです。モデルはSQLAlchemyのORMを用いて実装されています。  

### AttendanceRecord（勤怠レコード）

勤怠管理システムのメインテーブル。1日1レコードで、各日付の勤怠情報を格納します。  

- 勤怠入力・編集・集計・APIレスポンスの基礎となるテーブルです。
- `date`はユニーク制約があり、1日1レコードのみ登録可能です。
- `interruptions`はJSON形式で複数の中断時間帯を格納できます。
- `updated_at`はレコード作成・更新時に自動で現在日時が入ります（ローカルタイム）。
- `start_time`や`end_time`は文字列（"HH:MM"形式）で保存されます。
- `break_minutes`や`side_job_minutes`は分単位の整数値です。
- `comment`は任意の文字列を格納できます。

| カラム名          | 型         | 説明                                         | 制約                   |
|-------------------|------------|----------------------------------------------|------------------------|
| id                | Integer    | 主キー（自動採番）                           | primary_key, index     |
| date              | Date       | 勤怠対象日                                   | index, not null, unique|
| start_time        | String     | 勤務開始時刻（例: "09:00"）                  | nullable               |
| end_time          | String     | 勤務終了時刻（例: "18:00"）                  | nullable               |
| break_minutes     | Integer    | 休憩時間（分単位）                           | nullable               |
| interruptions     | JSON       | 中断時間リスト（例: [{"start": "12:00", "end": "13:00"}, ...]） | nullable               |
| side_job_minutes  | Integer    | 副業時間（分単位）                           | nullable               |
| updated_at        | DateTime   | 最終更新日時（レコード作成・更新時に自動設定）| default/auto-update    |
| comment           | String     | コメント・備考欄                              | nullable               |



## APIスキーマ仕様

- `interruptions`は`Interruption`型のリストで、各要素が中断の開始・終了時刻を持ちます。中断回数を可変とするためDBはJSONで保存するようにしているので、文字列としています。
- `start_time`と`end_time`は中断の文字列と合わせるために文字列にしています。フロントでの混乱を避けるためです。
- `AttendanceCreate`・`AttendanceUpdate`はAPIリクエストボディ用、`AttendanceOut`はAPIレスポンス用です。
- すべてPydanticのバリデーションが適用されます。

### Interruption（中断時間）

| フィールド名 | 型     | 説明                         | 必須 |
|--------------|--------|------------------------------|------|
| start        | str    | 中断開始時刻（"HH:MM"形式）  | ○    |
| end          | str    | 中断終了時刻（"HH:MM"形式）  | ○    |

### AttendanceBase（勤怠情報 共通部）

| フィールド名      | 型                        | 説明                                         | 必須 | 備考                |
|-------------------|---------------------------|----------------------------------------------|------|---------------------|
| start_time        | Optional[str]             | 勤務開始時刻（"HH:MM"形式）                  | ×    |                     |
| end_time          | Optional[str]             | 勤務終了時刻（"HH:MM"形式）                  | ×    |                     |
| break_minutes     | Optional[int]             | 休憩時間（分単位）                           | ×    |                     |
| interruptions     | Optional[List[Interruption]] | 中断時間リスト                               | ×    | デフォルトは空リスト |
| side_job_minutes  | Optional[int]             | 副業時間（分単位）                           | ×    |                     |
| updated_at        | Optional[datetime]        | 最終更新日時                                 | ×    |                     |
| comment           | Optional[str]             | コメント・備考欄                              | ×    |                     |

### AttendanceCreate（勤怠新規作成リクエスト用）

- AttendanceBaseを継承。追加フィールドなし。

### AttendanceUpdate（勤怠更新リクエスト用）

- AttendanceBaseを継承。追加フィールドなし。

### AttendanceOut（勤怠情報レスポンス用）

| フィールド名      | 型                        | 説明                                         | 必須 |
|-------------------|---------------------------|----------------------------------------------|------|
| date              | date                      | 勤怠日付                                     | ○    |
| ...               | AttendanceBaseの全フィールド | 上記参照                                     |      |

## 勤怠管理API エンドポイント仕様

API仕様はFastAPIで自動生成されます。[APIドキュメント localhost:8000/docs](localhost:8000/docs)


### ベースURL

```
http://<host>:8000/api
```

### 勤怠データCRUD

| メソッド | パス                                         | 概要                       | 主なレスポンス         |
|----------|----------------------------------------------|----------------------------|------------------------|
| GET      | /attendance/{record_date}                    | 指定日の勤怠データ取得      | AttendanceOut          |
| POST     | /attendance/{record_date}                    | 指定日の勤怠データ作成/更新 | AttendanceOut          |
| DELETE   | /attendance/{record_date}                    | 指定日の勤怠データ削除      | {"detail": "Deleted"}  |
| GET      | /attendance/month/{year_month}               | 指定月の勤怠データ一覧取得  | List[AttendanceOut]    |

### 勤怠サマリー

| メソッド | パス                                         | 概要                       | 主なレスポンス         |
|----------|----------------------------------------------|----------------------------|------------------------|
| GET      | /attendance/summary/12months                 | 直近12ヶ月の月次サマリー    | List[Summary]          |
| GET      | /attendance/summary/daily/{month}            | 指定月の日別サマリー        | List[DailySummary]     |

### 主なレスポンス構造

#### AttendanceOut

```json
{
  "date": "2024-06-01",
  "start_time": "09:00",
  "end_time": "18:00",
  "break_minutes": 60,
  "interruptions": [
    {"start": "12:00", "end": "13:00"}
  ],
  "side_job_minutes": 30,
  "updated_at": "2024-06-01T18:00:00",
  "comment": "備考"
}
```

#### Summary（/attendance/summary/12months）

```json
[
  {
    "month": "2024-06",
    "working_days": 20,
    "total_work_minutes": 9600
  }
]
```

#### DailySummary（/attendance/summary/daily/{month}）

```json
[
  {
    "date": "2024-06-01",
    "work_minutes": 480
  }
]
```
