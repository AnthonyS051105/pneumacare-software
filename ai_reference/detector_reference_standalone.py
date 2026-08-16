import torch
import torch.nn.functional as F
from .model import RespiratoryMobileNet, process_wav_to_segments
import os
import numpy as np

class Detector:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = ["none", "wheeze", "crackle", "both"]
        
        self.model = RespiratoryMobileNet(num_classes=4)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path tidak ditemukan di: {model_path}")
            
        checkpoint = torch.load(model_path, map_location=self.device)
        if "state_dict" in checkpoint:
            state_dict = {k.replace("model.", ""): v for k, v in checkpoint["state_dict"].items() if k.startswith("model.")}
            self.model.model.load_state_dict(state_dict)
        else:
            self.model.load_state_dict(checkpoint)
            
        self.model.to(self.device)
        self.model.eval()

    def predict(self, wav_path: str, overlap: float = 0.0):
        """
        Melakukan prediksi file audio .wav. 
        Jika durasi > 5 detik, mengembalikan sequence list berisi prediksi per rentang waktu 5 detik.
        Parameter overlap (dalam detik) menentukan tumpang tindih antar segmen (misal: overlap=2.5).
        """
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"File audio tidak ditemukan di: {wav_path}")

        segments = process_wav_to_segments(wav_path, overlap=overlap)
        results = []

        with torch.no_grad():
            for tensor_x, start_t, end_t in segments:
                tensor_x = tensor_x.to(self.device)
                logits = self.model(tensor_x)
                probabilities = F.softmax(logits, dim=1).cpu().numpy()[0]

                result_percentages = {
                    cls_name: float(probabilities[i] * 100) 
                    for i, cls_name in enumerate(self.classes)
                }
                
                predicted_idx = int(np.argmax(probabilities))
                best_label = self.classes[predicted_idx]

                results.append({
                    "start": start_t,
                    "end": end_t,
                    "prediction": best_label,
                    "confidence": float(probabilities[predicted_idx] * 100),
                    "probabilities": result_percentages
                })

        # Jika hanya ada 1 segmen (<= 5 detik), kembalikan langsung object dictionary-nya agar tetap backward-compatible
        if len(results) == 1:
            return results[0]
            
        return results