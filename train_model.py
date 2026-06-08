# ================================================
# 2단계: 전처리 모델 학습
# 흐린 사진 → 선명한 사진으로 복원하는 모델 학습
# (코랩 런타임을 GPU로 바꾸고 실행하세요!)
# ================================================

# ── 셀 1: GPU 확인 ──
import torch
print("GPU 사용 가능:", torch.cuda.is_available())
print("GPU 이름:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "없음 (런타임 → GPU로 변경하세요!)")

# ── 셀 2: 패키지 설치 ──
!pip install torch torchvision pillow opencv-python-headless -q

# ── 셀 3: 라이브러리 import ──
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"학습 장치: {DEVICE}")

# ── 셀 4: 데이터셋 클래스 ──
class BlurryCleanDataset(Dataset):
    """
    흐린 사진(blurry)과 선명한 사진(clean)을 쌍으로 불러오는 클래스
    """
    def __init__(self, clean_dir, blurry_dir, img_size=256):
        self.clean_dir = clean_dir
        self.blurry_dir = blurry_dir
        self.img_size = img_size

        # blurry 파일 목록 기준으로 쌍 만들기
        self.pairs = []
        for blurry_name in os.listdir(blurry_dir):
            if not blurry_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            # blurry 파일명에서 원본 파일명 찾기
            # 예: "doc1_gaussian.jpg" → "doc1.jpg"
            base = "_".join(blurry_name.split("_")[:-1])
            for ext in [".jpg", ".jpeg", ".png"]:
                clean_path = os.path.join(clean_dir, base + ext)
                if os.path.exists(clean_path):
                    self.pairs.append((
                        os.path.join(blurry_dir, blurry_name),
                        clean_path
                    ))
                    break

        print(f"데이터 쌍 {len(self.pairs)}개 로드 완료")

        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),  # 0~255 → 0~1
        ])

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        blurry_path, clean_path = self.pairs[idx]
        blurry = self.transform(Image.open(blurry_path).convert("RGB"))
        clean = self.transform(Image.open(clean_path).convert("RGB"))
        return blurry, clean

# ── 셀 5: 모델 구조 (간단한 CNN) ──
class DeblurNet(nn.Module):
    """
    흐린 사진을 입력받아 선명하게 복원하는 CNN 모델
    간단하지만 학습 잘 되는 구조로 설계했어요
    """
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1), nn.ReLU(),  # 1/2
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 256, 3, stride=2, padding=1), nn.ReLU(),  # 1/4
        )
        self.middle = nn.Sequential(
            nn.Conv2d(256, 256, 3, padding=1), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1), nn.ReLU(),  # x2
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1), nn.ReLU(),   # x2
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 3, 3, padding=1),
            nn.Sigmoid()  # 출력값 0~1로 고정
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.middle(x)
        x = self.decoder(x)
        return x

# ── 셀 6: 학습 준비 ──
BATCH_SIZE = 8
EPOCHS = 30
LEARNING_RATE = 0.001

dataset = BlurryCleanDataset("data/clean", "data/blurry")
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

model = DeblurNet().to(DEVICE)
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
loss_fn = nn.MSELoss()  # 선명한 사진과의 픽셀 차이를 줄이도록 학습

print(f"학습 시작 준비 완료!")
print(f"  배치 크기: {BATCH_SIZE}")
print(f"  에폭 수: {EPOCHS}")
print(f"  데이터 수: {len(dataset)}장")

# ── 셀 7: 학습 실행 ──
loss_history = []

for epoch in range(EPOCHS):
    model.train()
    epoch_loss = 0

    for blurry, clean in dataloader:
        blurry = blurry.to(DEVICE)
        clean = clean.to(DEVICE)

        output = model(blurry)
        loss = loss_fn(output, clean)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(dataloader)
    loss_history.append(avg_loss)

    if (epoch + 1) % 5 == 0:
        print(f"Epoch [{epoch+1}/{EPOCHS}]  Loss: {avg_loss:.4f}")

print("\n학습 완료!")

# ── 셀 8: 학습 곡선 확인 ──
plt.plot(loss_history)
plt.title("학습 Loss 변화")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.grid(True)
plt.show()

# ── 셀 9: 모델 저장 ──
torch.save(model.state_dict(), "deblur_model.pth")
print("모델 저장 완료: deblur_model.pth")

# 내 컴퓨터로 다운로드 (선택)
from google.colab import files
files.download("deblur_model.pth")

# ── 셀 10: 결과 미리보기 ──
model.eval()
blurry_sample, clean_sample = dataset[0]

with torch.no_grad():
    output = model(blurry_sample.unsqueeze(0).to(DEVICE)).squeeze(0).cpu()

def tensor_to_img(t):
    return (t.permute(1, 2, 0).numpy() * 255).astype(np.uint8)

fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].imshow(tensor_to_img(blurry_sample)); axes[0].set_title("입력 (흐린 사진)"); axes[0].axis("off")
axes[1].imshow(tensor_to_img(output));        axes[1].set_title("출력 (복원된 사진)"); axes[1].axis("off")
axes[2].imshow(tensor_to_img(clean_sample));  axes[2].set_title("정답 (원본 선명한 사진)"); axes[2].axis("off")
plt.tight_layout()
plt.show()
