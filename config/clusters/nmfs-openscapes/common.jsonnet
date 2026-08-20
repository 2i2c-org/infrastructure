local commonConfig = import './common.libsonnet';


local gpuAllowedGroups = [
  'nmfs-openscapes:gpu-access-2i2c',
  '2i2c-org:hub-access-for-2i2c-staff',
];

local defaultProfile = commonConfig.getDefaultProfile;
local gpu = commonConfig.getGPUProfile;

local restricted_gpu = gpu {
  allowed_groups: gpuAllowedGroups,
};

local profiles = [defaultProfile, restricted_gpu];

profiles
