# Default options

Part of being 'low touch' is to provide default options that we think might
work for most people. These are specified in `hub/values.yaml` in the repository.
We list some common ones here.

1. **Memory Limit** of 1G per student, with a guarantee of 256M. This means that
   everyone will be *guaranteed* 256M of memory, and most likely will have access
   to 1G of memory. But they can't use more than 1G of memory - their kernels and
   processes will die if they use more than this.
