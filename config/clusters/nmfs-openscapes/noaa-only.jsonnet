local commonConfig = import './common.libsonnet';

local defaultProfile = commonConfig.getDefaultProfile;
local gpu = commonConfig.getGPUProfile;

local profiles = [defaultProfile, gpu];

profiles
