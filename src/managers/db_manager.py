from pathlib import Path
import logging
from typing import Dict

class DatabaseManager:
    """Manages database setup and configuration"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
    def setup_database(self, requirements: Dict):
        """Setup database based on requirements"""
        try:
            db_type = self._determine_db_type(requirements)
            
            if db_type == 'prisma':
                self._setup_prisma()
            elif db_type == 'mongoose':
                self._setup_mongoose()
                
        except Exception as e:
            logging.error(f"Error setting up database: {str(e)}")
            
    def _determine_db_type(self, requirements: Dict) -> str:
        """Determine which database type to use"""
        if 'database' in requirements.get('features', []):
            if 'mongodb' in requirements.get('database', '').lower():
                return 'mongoose'
        return 'prisma'  # Default to Prisma with PostgreSQL
        
    def _setup_prisma(self):
        """Setup Prisma ORM"""
        # Create prisma directory
        prisma_dir = self.project_dir / "prisma"
        prisma_dir.mkdir(exist_ok=True)
        
        # Create schema.prisma
        schema = '''
datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")
}

generator client {
    provider = "prisma-client-js"
}

model User {
    id        String   @id @default(cuid())
    email     String   @unique
    name      String?
    password  String
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
    profile   Profile?
    posts     Post[]
}

model Profile {
    id     String  @id @default(cuid())
    bio    String?
    user   User    @relation(fields: [userId], references: [id])
    userId String  @unique
}

model Post {
    id        String   @id @default(cuid())
    title     String
    content   String?
    published Boolean  @default(false)
    author    User     @relation(fields: [authorId], references: [id])
    authorId  String
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
}
'''
        with open(prisma_dir / "schema.prisma", 'w') as f:
            f.write(schema)
            
        # Create initial migration
        self._create_migration("init")
        
    def _setup_mongoose(self):
        """Setup Mongoose ODM"""
        models_dir = self.project_dir / "src" / "models"
        models_dir.mkdir(exist_ok=True)
        
        # Create User model
        user_model = '''
import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
    email: { type: String, required: true, unique: true },
    name: String,
    password: { type: String, required: true },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

userSchema.pre('save', function(next) {
    this.updatedAt = new Date();
    next();
});

export const User = mongoose.models.User || mongoose.model('User', userSchema);
'''
        with open(models_dir / "user.ts", 'w') as f:
            f.write(user_model)
            
        # Create database connection utility
        db_config = '''
import mongoose from 'mongoose';

const MONGODB_URI = process.env.MONGODB_URI;

if (!MONGODB_URI) {
    throw new Error('Please define the MONGODB_URI environment variable');
}

let cached = global.mongoose;

if (!cached) {
    cached = global.mongoose = { conn: null, promise: null };
}

async function dbConnect() {
    if (cached.conn) {
        return cached.conn;
    }

    if (!cached.promise) {
        const opts = {
            bufferCommands: false,
        };

        cached.promise = mongoose.connect(MONGODB_URI!, opts).then((mongoose) => {
            return mongoose;
        });
    }
    cached.conn = await cached.promise;
    return cached.conn;
}

export default dbConnect;
'''
        with open(self.project_dir / "src" / "lib" / "dbConnect.ts", 'w') as f:
            f.write(db_config)
            
    def _create_migration(self, name: str):
        """Create a new database migration"""
        try:
            import subprocess
            subprocess.run(['npx', 'prisma', 'migrate', 'dev', '--name', name], 
                         cwd=self.project_dir, check=True)
        except Exception as e:
            logging.error(f"Error creating migration: {str(e)}")
            
    async def seed_database(self):
        """Seed the database with initial data"""
        seed_dir = self.project_dir / "prisma" / "seed"
        seed_dir.mkdir(exist_ok=True)
        
        seed_script = '''
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    // Create sample user
    const user = await prisma.user.create({
        data: {
            email: 'test@example.com',
            name: 'Test User',
            password: 'hashed_password', // In production, use proper password hashing
            profile: {
                create: {
                    bio: 'Sample bio',
                },
            },
        },
    });

    // Create sample post
    await prisma.post.create({
        data: {
            title: 'Hello World',
            content: 'This is a sample post.',
            authorId: user.id,
        },
    });
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
'''
        with open(seed_dir / "seed.ts", 'w') as f:
            f.write(seed_script) 