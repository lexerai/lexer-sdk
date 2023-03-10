# Third party imports
import torch.onnx
import torch.utils.model_zoo as model_zoo
from torch import nn
from torch.nn import init

# Lexer imports
from lexer.api.lexer_context import LexerContext
from lexer.decorators.lexer import Lexer


@Lexer(
    input_names=["input"],
    output_names=["output"],
)
class SuperResolutionNet(nn.Module):
    def __init__(self, upscale_factor, inplace=False):
        super(SuperResolutionNet, self).__init__()

        self.relu = nn.ReLU(inplace=inplace)
        self.conv1 = nn.Conv2d(1, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = nn.Conv2d(32, upscale_factor**2, (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

        self._initialize_weights()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x

    def _initialize_weights(self):
        init.orthogonal_(self.conv1.weight, init.calculate_gain("relu"))
        init.orthogonal_(self.conv2.weight, init.calculate_gain("relu"))
        init.orthogonal_(self.conv3.weight, init.calculate_gain("relu"))
        init.orthogonal_(self.conv4.weight)


if __name__ == "__main__":
    # ----------------------- USER CODE START ------------------------------
    # Create the super-resolution model by using the above model definition.
    torch_model = SuperResolutionNet(upscale_factor=3)

    # Load pretrained model weights
    model_url = "https://s3.amazonaws.com/pytorch/test_data/export/superres_epoch100-44c6958e.pth"  # noqa: E501
    batch_size = 1  # just a random number

    # Initialize model with the pretrained weights
    map_location = lambda storage, loc: storage  # noqa: E731
    if torch.cuda.is_available():
        map_location = None
    torch_model.load_state_dict(
        model_zoo.load_url(model_url, map_location=map_location)
    )

    # set the model to inference mode
    torch_model.eval()

    # Input to the model
    input_tensor = torch.randn(batch_size, 1, 224, 224, requires_grad=True)

    # ------------------------ USER CODE END ---------------------------------

    lexer_context = LexerContext()

    # lexer_context.export(torch_model=torch_model, input=input_tensor)
    lexer_context.benchmark(
        torch_model=torch_model,
        input=input_tensor,
        num_iterations=5,  # These are "optional" arguments
        batch_size=batch_size,
    )
    # This is needed to generate the Lexer artifact.
    lexer_context.flush(name="benchmark", target_directory=".")

    # print("OpenAPI JSON:")
    # print(torch_model.lexer.schema_json(indent=2))  # type: ignore
