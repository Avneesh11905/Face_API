
import dlib
print("Using CUDA:", dlib.DLIB_USE_CUDA)  # Should print True
print("Number of CUDA devices:", dlib.cuda.get_num_devices())  # Should print the number of GPUs
