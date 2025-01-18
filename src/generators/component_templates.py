from typing import Dict

class ComponentTemplates:
    """Stores and manages component templates"""
    
    @staticmethod
    def get_template(component_type: str, features: Dict) -> str:
        """Get the appropriate template for a component type"""
        if component_type in COMPONENT_TEMPLATES:
            return COMPONENT_TEMPLATES[component_type]
        return COMPONENT_TEMPLATES['default']

# Template constants
COMPONENT_TEMPLATES = {
    'default': '''
import React from 'react';
import styles from './{{name}}.module.css';

interface {{name}}Props {
    children?: React.ReactNode;
}

export const {{name}}: React.FC<{{name}}Props> = ({ children }) => {
    return (
        <div className={styles.container}>
            {children}
        </div>
    );
};
''',
    
    'layout': '''
import React from 'react';
import styles from './{{name}}.module.css';

interface {{name}}Props {
    children: React.ReactNode;
    className?: string;
}

export const {{name}}: React.FC<{{name}}Props> = ({ 
    children,
    className = ''
}) => {
    return (
        <div className={`${styles.layout} ${className}`}>
            {children}
        </div>
    );
};
''',

    'form': '''
import React from 'react';
import { useForm } from 'react-hook-form';
import styles from './{{name}}.module.css';

interface {{name}}Props {
    onSubmit: (data: any) => void;
}

export const {{name}}: React.FC<{{name}}Props> = ({ onSubmit }) => {
    const { register, handleSubmit, formState: { errors } } = useForm();

    return (
        <form className={styles.form} onSubmit={handleSubmit(onSubmit)}>
            {/* Form fields will be added here */}
        </form>
    );
};
''',

    'interactive': '''
import React, { useState } from 'react';
import styles from './{{name}}.module.css';

interface {{name}}Props {
    onAction?: () => void;
}

export const {{name}}: React.FC<{{name}}Props> = ({ onAction }) => {
    const [isActive, setIsActive] = useState(false);

    const handleClick = () => {
        setIsActive(!isActive);
        onAction?.();
    };

    return (
        <div 
            className={`${styles.container} ${isActive ? styles.active : ''}`}
            onClick={handleClick}
        >
            {/* Interactive content will be added here */}
        </div>
    );
};
'''
}

# CSS Templates
CSS_TEMPLATES = {
    'default': '''
.container {
    display: flex;
    flex-direction: column;
    padding: 1rem;
}
''',

    'layout': '''
.layout {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}
''',

    'form': '''
.form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 500px;
    margin: 0 auto;
}
''',

    'interactive': '''
.container {
    cursor: pointer;
    transition: all 0.3s ease;
}

.active {
    transform: scale(1.05);
}
'''
} 