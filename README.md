# baby-cost-jp

ベビー用品を「商品価格」ではなく、1枚・100gなどの共通単位に換算して比較する静的サイトMVPです。

## MVPカテゴリー

- 紙おむつ: テープ/パンツ × サイズ別、1枚あたり
- おしりふき: 1枚あたり
- 乳児用粉ミルク: 100gあたり
- おむつ用防臭・消臭袋: 1枚あたり

## 設計原則

1. 条件違いの商品を同じランキングに混ぜない。
2. 数量を安全に解析できない商品は表示しない。
3. 単価の計算根拠と解析信頼度を表示する。
4. 価格以外の品質・健康・相性を根拠なく順位付けしない。
5. 商品データ取得、数量解析、単価計算、UI、Analyticsを分離する。

## ローカル確認

```bash
python -m unittest discover -s tests -v
python scripts/build_site.py --fixture
python -m http.server 8000 -d site
```

## 本番ビルド

必要な環境変数:

- `RAKUTEN_APPLICATION_ID`
- `RAKUTEN_ACCESS_KEY`
- `RAKUTEN_AFFILIATE_ID`
- `GA_MEASUREMENT_ID`
- `SITE_URL`（省略時 `https://stusaurus.github.io/baby-cost-jp/`）

```bash
python scripts/build_site.py --pages 2
```

GitHub Actionsは毎日06:17 JSTに価格データを更新し、GitHub Pagesへデプロイします。

## 公開設定

Repository Settings > Secrets and variables > Actions に上記Secretsを追加し、Settings > Pages の Source を GitHub Actions に設定します。

## 比較範囲

楽天APIで「送料込み／送料無料」に絞って取得した候補商品のうち、条件と数量を安全に確認できた商品を比較します。「市場全体の絶対最安」ではなく「取得比較対象内の単価順」です。ポイント・クーポンはMVPの順位計算に含めません。比較対象が2件未満のページはnoindexにし、sitemapにも載せません。
