module "c7n" {
  source             = "./modules/c7n"
  instance_role_name = "AppfireCloudCustodian"
  sqs_parameter_name = "/c7n/queue_arn"
}

module "deployment" {
  source           = "./modules/deployment"
  aws_region       = var.aws_region
  environment      = var.environment
  instance_type    = var.instance_type
  instance_profile = module.c7n.instance_profile_name
}
