import { Request, Response, NextFunction } from 'express';
import Joi from 'joi';

export const validateRequest = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation error',
        details: error.details.map(detail => detail.message)
      });
    }
    
    next();
  };
};

export const schemas = {
  register: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).required(),
    name: Joi.string().min(2).max(100).required(),
    role: Joi.string().valid('admin', 'analyst', 'viewer').default('viewer')
  }),

  login: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
  }),

  hotspot: Joi.object({
    title: Joi.string().min(1).max(255).required(),
    description: Joi.string().max(1000),
    latitude: Joi.number().min(-90).max(90).required(),
    longitude: Joi.number().min(-180).max(180).required(),
    severity: Joi.string().valid('low', 'medium', 'high', 'critical').required(),
    event_type: Joi.string().valid('earthquake', 'flood', 'fire', 'storm', 'other').required()
  }),

  factCheck: Joi.object({
    content: Joi.string().min(10).max(5000).required(),
    url: Joi.string().uri().optional()
  })
};