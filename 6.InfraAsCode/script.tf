provider "aws" {
  region = "us-east-1"  #valor fictício
}

resource "aws_iam_role" "glue_service_role" {
  name = "glue_service_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "glue.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_attach" {
  role       = aws_iam_role.glue_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_glue_job" "cliente_analise" {
  name     = "cliente-analise-job"
  role_arn = aws_iam_role.glue_service_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://bucket-codes/scripts/analise_clientes.py" #valor fictício
    python_version  = "3"
  }

  max_capacity        = 10
  worker_type         = "G.1X"
  number_of_workers   = 10
  glue_version        = "5.0"
  timeout             = 60
  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    projeto = "teste_eng_dados"
  }
}
