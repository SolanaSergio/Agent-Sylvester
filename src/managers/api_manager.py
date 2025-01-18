from typing import Dict, List, Optional
import logging
from pathlib import Path
import json

class APIManager:
    """Manages API integrations and configurations"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.api_dir = project_dir / "src" / "api"
        self.api_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_api_layer(self, requirements: Dict):
        """Setup API integration layer based on requirements"""
        try:
            # Create API directory structure
            self._create_api_structure()
            
            # Generate API utilities
            self._generate_api_utils()
            
            # Generate API endpoints
            if 'features' in requirements:
                self._generate_feature_endpoints(requirements['features'])
                
        except Exception as e:
            logging.error(f"Error setting up API layer: {str(e)}")
            
    def _create_api_structure(self):
        """Create API directory structure"""
        (self.api_dir / "endpoints").mkdir(exist_ok=True)
        (self.api_dir / "middleware").mkdir(exist_ok=True)
        (self.api_dir / "utils").mkdir(exist_ok=True)
        
    def _generate_api_utils(self):
        """Generate API utility files"""
        utils_dir = self.api_dir / "utils"
        
        # Generate API client
        client_code = '''
import axios from 'axios';

const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor for authentication
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized access
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default apiClient;
'''
        with open(utils_dir / "apiClient.ts", 'w') as f:
            f.write(client_code)
            
        # Generate API response utilities
        response_utils = '''
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
}

export const createSuccessResponse = <T>(data: T): ApiResponse<T> => ({
    success: true,
    data,
});

export const createErrorResponse = (error: string): ApiResponse => ({
    success: false,
    error,
});
'''
        with open(utils_dir / "apiResponse.ts", 'w') as f:
            f.write(response_utils)
            
    def _generate_feature_endpoints(self, features: List[str]):
        """Generate API endpoints for features"""
        endpoints_dir = self.api_dir / "endpoints"
        
        if 'authentication' in features:
            self._generate_auth_endpoints()
            
        if 'database' in features:
            self._generate_data_endpoints()
            
    def _generate_auth_endpoints(self):
        """Generate authentication endpoints"""
        auth_dir = self.api_dir / "endpoints" / "auth"
        auth_dir.mkdir(exist_ok=True)
        
        # Generate login endpoint
        login_endpoint = '''
import { NextApiRequest, NextApiResponse } from 'next';
import { createSuccessResponse, createErrorResponse } from '../../utils/apiResponse';
import { withAuth } from '../../middleware/auth';
import { prisma } from '../../lib/prisma';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

async function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method !== 'POST') {
        return res.status(405).json(createErrorResponse('Method not allowed'));
    }

    try {
        const { email, password } = req.body;

        const user = await prisma.user.findUnique({ where: { email } });
        if (!user) {
            return res.status(401).json(createErrorResponse('Invalid credentials'));
        }

        const isValid = await bcrypt.compare(password, user.password);
        if (!isValid) {
            return res.status(401).json(createErrorResponse('Invalid credentials'));
        }

        const token = jwt.sign(
            { userId: user.id },
            process.env.JWT_SECRET!,
            { expiresIn: '7d' }
        );

        return res.status(200).json(createSuccessResponse({ token }));
    } catch (error) {
        console.error('Login error:', error);
        return res.status(500).json(createErrorResponse('Internal server error'));
    }
}

export default handler;
'''
        with open(auth_dir / "login.ts", 'w') as f:
            f.write(login_endpoint)
            
        # Generate middleware
        middleware_dir = self.api_dir / "middleware"
        middleware_dir.mkdir(exist_ok=True)
        
        auth_middleware = '''
import { NextApiRequest, NextApiResponse } from 'next';
import jwt from 'jsonwebtoken';
import { createErrorResponse } from '../utils/apiResponse';

export interface AuthenticatedRequest extends NextApiRequest {
    user?: {
        userId: string;
    };
}

export function withAuth(
    handler: (req: AuthenticatedRequest, res: NextApiResponse) => Promise<void>
) {
    return async (req: AuthenticatedRequest, res: NextApiResponse) => {
        try {
            const token = req.headers.authorization?.replace('Bearer ', '');
            
            if (!token) {
                return res.status(401).json(createErrorResponse('Unauthorized'));
            }

            const decoded = jwt.verify(token, process.env.JWT_SECRET!) as { userId: string };
            req.user = decoded;

            return handler(req, res);
        } catch (error) {
            return res.status(401).json(createErrorResponse('Invalid token'));
        }
    };
}
'''
        with open(middleware_dir / "auth.ts", 'w') as f:
            f.write(auth_middleware)
            
    def _generate_data_endpoints(self):
        """Generate data endpoints"""
        data_dir = self.api_dir / "endpoints" / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Generate user endpoints
        user_endpoint = '''
import { NextApiRequest, NextApiResponse } from 'next';
import { createSuccessResponse, createErrorResponse } from '../../utils/apiResponse';
import { withAuth, AuthenticatedRequest } from '../../middleware/auth';
import { prisma } from '../../lib/prisma';

async function handler(req: AuthenticatedRequest, res: NextApiResponse) {
    switch (req.method) {
        case 'GET':
            return handleGet(req, res);
        case 'PUT':
            return handlePut(req, res);
        default:
            return res.status(405).json(createErrorResponse('Method not allowed'));
    }
}

async function handleGet(req: AuthenticatedRequest, res: NextApiResponse) {
    try {
        const user = await prisma.user.findUnique({
            where: { id: req.user!.userId },
            include: { profile: true },
        });

        if (!user) {
            return res.status(404).json(createErrorResponse('User not found'));
        }

        const { password, ...userData } = user;
        return res.status(200).json(createSuccessResponse(userData));
    } catch (error) {
        console.error('Get user error:', error);
        return res.status(500).json(createErrorResponse('Internal server error'));
    }
}

async function handlePut(req: AuthenticatedRequest, res: NextApiResponse) {
    try {
        const { name, bio } = req.body;

        const user = await prisma.user.update({
            where: { id: req.user!.userId },
            data: {
                name,
                profile: {
                    upsert: {
                        create: { bio },
                        update: { bio },
                    },
                },
            },
            include: { profile: true },
        });

        const { password, ...userData } = user;
        return res.status(200).json(createSuccessResponse(userData));
    } catch (error) {
        console.error('Update user error:', error);
        return res.status(500).json(createErrorResponse('Internal server error'));
    }
}

export default withAuth(handler);
'''
        with open(data_dir / "user.ts", 'w') as f:
            f.write(user_endpoint) 