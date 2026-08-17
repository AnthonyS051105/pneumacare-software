import torch

from ai_reference.model import RespiratoryMobileNet
from backend.inference.model_loader import load_model


def test_load_model_raises_file_not_found_for_missing_checkpoint():
    try:
        load_model("/path/yang/pasti/tidak/ada/checkpoint.ckpt")
        assert False, "seharusnya raise FileNotFoundError"
    except FileNotFoundError as exc:
        assert "tidak ditemukan" in str(exc)


def test_load_model_with_synthetic_checkpoint(tmp_path):
    """Bikin checkpoint sintetis dengan struktur PERSIS seperti PyTorch Lightning
    (key berawalan "model.") supaya jalur load_state_dict-nya benar-benar teruji,
    tanpa perlu checkpoint asli dari Nathanael."""
    reference_model = RespiratoryMobileNet(num_classes=4)
    state_dict_with_prefix = {f"model.{k}": v for k, v in reference_model.model.state_dict().items()}
    checkpoint_path = tmp_path / "synthetic_checkpoint.ckpt"
    torch.save({"state_dict": state_dict_with_prefix}, checkpoint_path)

    loaded_model = load_model(str(checkpoint_path), device=torch.device("cpu"))

    assert isinstance(loaded_model, RespiratoryMobileNet)
    assert loaded_model.training is False  # harus dalam mode eval()

    # bobot yang dimuat harus identik dengan reference (verifikasi load_state_dict
    # ke model.model, bukan model langsung, benar-benar berhasil)
    for (name, ref_param), (_, loaded_param) in zip(
        reference_model.model.named_parameters(), loaded_model.model.named_parameters()
    ):
        assert torch.equal(ref_param, loaded_param), f"parameter {name} tidak cocok setelah load"


def test_load_model_output_shape_matches_num_classes(tmp_path):
    reference_model = RespiratoryMobileNet(num_classes=4)
    state_dict_with_prefix = {f"model.{k}": v for k, v in reference_model.model.state_dict().items()}
    checkpoint_path = tmp_path / "synthetic_checkpoint.ckpt"
    torch.save({"state_dict": state_dict_with_prefix}, checkpoint_path)

    loaded_model = load_model(str(checkpoint_path), device=torch.device("cpu"))

    dummy_input = torch.randn(1, 1, 50, 216)  # shape [1,1,50,T] sesuai SDD_SOFTWARE.md §5
    with torch.no_grad():
        output = loaded_model(dummy_input)

    assert output.shape == (1, 4)
