# 用語集

```{glossary}
スキニング
    Mesh の頂点を複数のノードでかさみ付けして移動回転変形させる。

ジョイント
    位置だけ。スキニングするときのノードを呼ぶ

ボーン
    位置 + 方向(初期姿勢でのスケールは不許可)

ボーンローカル座標
    ボーンのXYZ軸が作る空間。
    スキニングに必要なJoint位置を原点に持ち任意の方向を持つ。
    VRM1 ではヒューマノイドボーンは T-Pose にしたとき 一定のルールに従うことを要求する(予定)。

ボーンローカルEuler角
    ボーンローカル座標に対するZXYEuler角。
```
